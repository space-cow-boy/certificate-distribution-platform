"""Certificate Generator Module.

Generates a PDF certificate by drawing the student name onto a template image using Pillow.

Key features:
- Dynamic centering (no hardcoded X)
- Dynamic font resizing to keep long names within margins
- Uses draw.textbbox() for accurate text measurement
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


class CertificateGenerator:
    """Generate personalized certificates from an image template and export as PDF."""

    def __init__(self, template_path: str = "templates/certificate_template.jpg", output_dir: Optional[str] = "certificates", management_template_path: str = "templates/CertificateManagement.jpeg"):
        project_root = Path(__file__).resolve().parents[1]

        template_candidate = Path((template_path or "").replace("\\", "/"))
        if not template_candidate.is_absolute():
            template_candidate = project_root / template_candidate
        self.template_path = str(template_candidate)

        self._project_root = project_root
        if output_dir is None:
            self.output_dir = None
        else:
            output_candidate = Path((output_dir or "").replace("\\", "/"))
            if not output_candidate.is_absolute():
                output_candidate = project_root / output_candidate
            self.output_dir = str(output_candidate)
            os.makedirs(self.output_dir, exist_ok=True)
        
        # Management certificate template
        if management_template_path:
            mgmt_candidate = Path((management_template_path or "").replace("\\", "/"))
            if not mgmt_candidate.is_absolute():
                mgmt_candidate = project_root / mgmt_candidate
            self.management_template_path = str(mgmt_candidate)
        else:
            self.management_template_path = None

    def _resolve_font_path(self) -> Optional[str]:
        """Resolve a TTF/OTF font path (recommended) to enable resizing."""
        env_font = (os.getenv("CERT_FONT_PATH") or "").strip()
        if env_font:
            p = Path(env_font.replace("\\", "/"))
            if not p.is_absolute():
                p = self._project_root / p
            if p.exists() and p.is_file():
                return str(p)

        candidates = [
            self._project_root / "templates" / "DejaVuSans-Bold.ttf",
            self._project_root / "templates" / "DejaVuSans.ttf",
            self._project_root / "templates" / "fonts" / "DejaVuSans-Bold.ttf",
            self._project_root / "templates" / "fonts" / "DejaVuSans.ttf",
            self._project_root / "templates" / "PlayfairDisplay-Bold.ttf",
            self._project_root / "templates" / "fonts" / "PlayfairDisplay-Bold.ttf",
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                return str(c)

        # System font fallbacks (more reliable when using absolute paths)
        system_candidates = [
            # Common Linux paths
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            # Common Windows paths
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/PlayfairDisplay-Bold.ttf",
        ]
        for path in system_candidates:
            try:
                if Path(path).exists():
                    return path
            except Exception:
                continue

        # As a last resort, try a few font names (works only if available in CWD or
        # resolved by the runtime environment).
        for name in ["PlayfairDisplay-Bold.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "arialbd.ttf", "arial.ttf", "Arial.ttf"]:
            try:
                ImageFont.truetype(name, 12)
                return name
            except Exception:
                continue

        return None

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        font_path = self._resolve_font_path()
        if not font_path:
            raise RuntimeError(
                "No TrueType/OpenType font found for dynamic resizing. "
                "Add a .ttf file and set CERT_FONT_PATH (e.g., templates/DejaVuSans-Bold.ttf)."
            )
        return ImageFont.truetype(font_path, size=size)

    @staticmethod
    def _fit_text(draw: ImageDraw.ImageDraw, text: str, *, max_width: int, start_size: int, min_size: int) -> ImageFont.FreeTypeFont:
        """Return a font resized so that text width <= max_width.

        If even min_size doesn't fit, this will still return min_size; caller can truncate.
        """
        size = start_size
        generator = getattr(draw, "_certificate_generator", None)
        if generator is None:
            raise RuntimeError("Internal error: generator context missing")

        while size >= min_size:
            font = generator._load_font(size)
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            width = right - left
            if width <= max_width:
                return font
            size -= 2

        return generator._load_font(min_size)

    @staticmethod
    def _truncate_to_fit(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
        """Truncate with ellipsis if needed to ensure no overflow."""
        ellipsis = "…"
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        if (right - left) <= max_width:
            return text

        base = text.strip()
        if not base:
            return ""

        lo, hi = 0, len(base)
        best = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            candidate = (base[:mid].rstrip() + ellipsis) if mid < len(base) else base
            l, t, r, b = draw.textbbox((0, 0), candidate, font=font)
            if (r - l) <= max_width:
                best = candidate
                lo = mid + 1
            else:
                hi = mid - 1
        return best or ellipsis
    
    def _draw_text_with_letter_spacing(self, draw: ImageDraw.ImageDraw, position: tuple, text: str, font: ImageFont.FreeTypeFont, fill: tuple, letter_spacing: float) -> None:
        """Draw text with custom letter spacing.
        
        Args:
            draw: ImageDraw object
            position: (x, y) tuple for starting position
            text: Text to draw
            font: Font to use
            fill: Color tuple
            letter_spacing: Letter spacing as decimal (e.g., 0.015 = 1.5%)
        """
        x, y = position
        
        # Get character width for spacing calculation
        for char in text:
            draw.text((x, y), char, font=font, fill=fill)
            char_bbox = draw.textbbox((x, y), char, font=font)
            char_width = char_bbox[2] - char_bbox[0]
            spacing_px = int(char_width * letter_spacing)
            x += char_width + spacing_px

    def generate_certificate(self, student_name: str, certificate_id: str, course: Optional[str] = None) -> str:
        if not self.output_dir:
            raise RuntimeError("Output directory is not configured")

        if not os.path.exists(self.template_path):
            raise FileNotFoundError(f"Template image not found: {self.template_path}")

        output_filename = f"{certificate_id}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)

        with Image.open(self.template_path) as img_in:
            img = img_in.convert("RGBA")
            draw = ImageDraw.Draw(img)

            # Attach generator context for helpers
            setattr(draw, "_certificate_generator", self)

            width, height = img.size

            # Layout controls
            margin_px = os.getenv("CERT_NAME_MARGIN_PX")
            if margin_px and margin_px.strip().isdigit():
                margin = int(margin_px)
            else:
                margin_ratio = float(os.getenv("CERT_NAME_MARGIN_RATIO", "0.12"))
                margin = int(width * margin_ratio)
            max_text_width = max(1, width - 2 * margin)

            # Font sizing: start relative to image width, with env overrides
            start_size = int(os.getenv("CERT_NAME_FONT_SIZE", str(max(24, int(width * 0.06)))))
            min_size = int(os.getenv("CERT_NAME_MIN_FONT_SIZE", "14"))

            # Positioning (centered horizontally, adjustable vertically)
            # Default places name below the "presented to" line on the template.
            # Tune via CERT_NAME_Y_RATIO (0..1) or CERT_NAME_Y_OFFSET (pixels).
            y_ratio = float(os.getenv("CERT_NAME_Y_RATIO", "0.52"))
            y_offset = float(os.getenv("CERT_NAME_Y_OFFSET", "0"))
            center_y = (height * y_ratio) + y_offset

            # Styling
            color_hex = (os.getenv("CERT_NAME_COLOR", "#000000") or "#000000").strip()
            if color_hex.startswith("#") and len(color_hex) in (7, 9):
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                a = int(color_hex[7:9], 16) if len(color_hex) == 9 else 255
                name_color = (r, g, b, a)
            else:
                name_color = (0, 0, 0, 255)

            name = (student_name or "").strip()
            if not name:
                raise ValueError("Student name is empty")

            font = self._fit_text(draw, name, max_width=max_text_width, start_size=start_size, min_size=min_size)
            name = self._truncate_to_fit(draw, name, font, max_text_width)

            left, top, right, bottom = draw.textbbox((0, 0), name, font=font)
            text_w = right - left
            text_h = bottom - top

            # Compute centered position (no hardcoded x)
            x = (width - text_w) / 2 - left
            y = (center_y - (text_h / 2)) - top

            # Safety clamp within margins
            x = max(margin, min(x, (width - margin - text_w)))

            draw.text((x, y), name, font=font, fill=name_color)

            # Draw course if provided
            if course and course.strip():
                course = course.strip()
                # Use smaller font for course
                course_font_size = max(min_size, int(start_size * 0.6))
                course_font = self._load_font(course_font_size)
                course = self._truncate_to_fit(draw, course, course_font, max_text_width)
                
                left_c, top_c, right_c, bottom_c = draw.textbbox((0, 0), course, font=course_font)
                text_w_c = right_c - left_c
                text_h_c = bottom_c - top_c
                
                # Position below name with some padding
                padding = int(height * 0.02)  # 2% of height
                y_c = y + text_h + padding - top_c
                x_c = (width - text_w_c) / 2 - left_c
                x_c = max(margin, min(x_c, (width - margin - text_w_c)))
                
                draw.text((x_c, y_c), course, font=course_font, fill=name_color)
            if img.mode != "RGB":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                out_img = background
            else:
                out_img = img

            out_img.save(output_path, "PDF", resolution=300.0)

        return output_path
    
    def certificate_exists(self, certificate_id: str) -> bool:
        """
        Check if certificate already exists
        
        Args:
            certificate_id: Certificate ID to check
            
        Returns:
            True if certificate exists, False otherwise
        """
        if not self.output_dir:
            return False

        output_path = os.path.join(self.output_dir, f"{certificate_id}.pdf")
        return os.path.exists(output_path)
    
    def get_certificate_path(self, certificate_id: str) -> str:
        """
        Get the path to a certificate
        
        Args:
            certificate_id: Certificate ID
            
        Returns:
            Path to the certificate PDF
        """
        if not self.output_dir:
            raise RuntimeError("Output directory is not configured")

        return os.path.join(self.output_dir, f"{certificate_id}.pdf")
    
    def generate_management_certificate(self, person_name: str, certificate_id: str) -> str:
        """
        Generate a management certificate (name only, no course)
        
        Args:
            person_name: The person's name
            certificate_id: Certificate ID for the filename
            
        Returns:
            Path to the generated PDF certificate
        """
        if not self.output_dir:
            raise RuntimeError("Output directory is not configured")

        # Use management template if available, otherwise use regular template
        template = self.management_template_path or self.template_path
        
        if not os.path.exists(template):
            raise FileNotFoundError(f"Template image not found: {template}")

        output_filename = f"{certificate_id}.pdf"
        output_path = os.path.join(self.output_dir, output_filename)

        with Image.open(template) as img_in:
            img = img_in.convert("RGBA")
            draw = ImageDraw.Draw(img)

            # Attach generator context for helpers
            setattr(draw, "_certificate_generator", self)

            width, height = img.size

            # Layout controls - use management-specific env vars if available
            margin_px = os.getenv("CERT_MGMT_NAME_MARGIN_PX") or os.getenv("CERT_NAME_MARGIN_PX")
            if margin_px and margin_px.strip().isdigit():
                margin = int(margin_px)
            else:
                margin_ratio = float(os.getenv("CERT_MGMT_NAME_MARGIN_RATIO", os.getenv("CERT_NAME_MARGIN_RATIO", "0.12")))
                margin = int(width * margin_ratio)
            max_text_width = max(1, width - 2 * margin)

            # Font sizing: management uses fixed 55px (increased from 50), students use dynamic
            start_size = int(os.getenv("CERT_MGMT_NAME_FONT_SIZE", "55"))
            min_size = int(os.getenv("CERT_MGMT_NAME_MIN_FONT_SIZE", "45"))
            
            # Positioning - management-specific
            y_ratio = float(os.getenv("CERT_MGMT_NAME_Y_RATIO", "0.52"))
            y_offset = float(os.getenv("CERT_MGMT_NAME_Y_OFFSET", "-134"))
            x_offset = float(os.getenv("CERT_MGMT_NAME_X_OFFSET", "5"))   # 5px to the right (moved 8px left from 13)
            center_y = (height * y_ratio) + y_offset
            
            # Letter spacing: management uses +1.5%
            letter_spacing = float(os.getenv("CERT_MGMT_LETTER_SPACING", "0.015"))  # 1.5%
            
            # Color - management-specific or fallback
            color_hex = (os.getenv("CERT_MGMT_NAME_COLOR", os.getenv("CERT_NAME_COLOR", "#000000")) or "#000000").strip()
            if color_hex.startswith("#") and len(color_hex) in (7, 9):
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                a = int(color_hex[7:9], 16) if len(color_hex) == 9 else 255
                name_color = (r, g, b, a)
            else:
                name_color = (0, 0, 0, 255)

            name = (person_name or "").strip()
            if not name:
                raise ValueError("Person name is empty")

            font = self._fit_text(draw, name, max_width=max_text_width, start_size=start_size, min_size=min_size)
            name = self._truncate_to_fit(draw, name, font, max_text_width)

            left, top, right, bottom = draw.textbbox((0, 0), name, font=font)
            text_w = right - left
            text_h = bottom - top

            x = (width - text_w) / 2 - left
            y = (center_y - (text_h / 2)) - top

            x = max(margin, min(x, (width - margin - text_w)))
            
            # Apply horizontal offset (move right)
            x += x_offset

            # Draw text with letter spacing
            self._draw_text_with_letter_spacing(draw, (x, y), name, font=font, fill=name_color, letter_spacing=letter_spacing)

            if img.mode != "RGB":
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                out_img = background
            else:
                out_img = img

            out_img.save(output_path, "PDF", resolution=300.0)

        return output_path

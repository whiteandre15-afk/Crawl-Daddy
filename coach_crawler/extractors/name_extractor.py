import re


class NameExtractor:
    """Parse and split full names into first/last components."""

    # Common prefixes/suffixes to strip
    PREFIXES = {"dr", "dr.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "coach", "prof", "prof."}
    SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "phd", "ph.d.", "ed.d.", "m.ed."}

    def parse(self, full_name: str | None) -> dict:
        """Parse full name into components.

        Returns: {full_name, first_name, last_name}
        """
        if not full_name:
            return {"full_name": None, "first_name": None, "last_name": None}

        cleaned = re.sub(r'\s+', ' ', full_name.strip())
        if not cleaned:
            return {"full_name": None, "first_name": None, "last_name": None}

        parts = cleaned.split()

        # Strip prefixes
        while parts and parts[0].lower().rstrip(".") in {p.rstrip(".") for p in self.PREFIXES}:
            parts = parts[1:]

        # Strip suffixes
        while parts and parts[-1].lower().rstrip(".,") in {s.rstrip(".") for s in self.SUFFIXES}:
            parts = parts[:-1]

        if not parts:
            return {"full_name": cleaned, "first_name": None, "last_name": None}

        if len(parts) == 1:
            return {"full_name": cleaned, "first_name": parts[0], "last_name": None}

        return {
            "full_name": cleaned,
            "first_name": parts[0],
            "last_name": parts[-1],
        }

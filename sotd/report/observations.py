"""Automated observations generator for hardware reports."""

from typing import Any, Dict, List, Optional, Tuple


class ObservationsGenerator:
    """Generate automated observations about hardware data trends."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        data: Dict[str, Any],
        comparison_data: Optional[Dict[str, Tuple[Dict[str, Any], Dict[str, Any]]]] = None,
    ):
        """Initialize the observations generator.

        Args:
            metadata: Current month metadata
            data: Current month data
            comparison_data: Historical data for trend analysis
        """
        self.metadata = metadata
        self.data = data
        self.comparison_data = comparison_data or {}

    def generate_observations(self) -> str:
        """Generate comprehensive observations about the data."""
        observations = []
        observations.append("## Observations\n\n")

        # Basic statistics
        observations.extend(self._generate_basic_statistics())

        # Top performers
        observations.extend(self._generate_top_performers())

        # Notable trends
        if self.comparison_data:
            observations.extend(self._generate_trend_analysis())

        # Format distribution
        observations.extend(self._generate_format_insights())

        # User engagement
        observations.extend(self._generate_user_insights())

        return "\n".join(observations)

    def _generate_basic_statistics(self) -> List[str]:
        """Generate basic statistics observations."""
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)
        avg_shaves_per_user = self.metadata.get("avg_shaves_per_user", 0)

        observations = []
        observations.append(
            f"This month saw **{total_shaves:,} shaves** from **{unique_shavers} unique users**, "
        )
        observations.append(f"averaging **{avg_shaves_per_user:.1f} shaves per user**.\n")

        return observations

    def _generate_top_performers(self) -> List[str]:
        """Generate observations about top performing products."""
        observations = []

        # Top razors
        if "razors" in self.data and self.data["razors"]:
            top_razor = self.data["razors"][0]
            if "name" in top_razor and "shaves" in top_razor and "unique_users" in top_razor:
                name = top_razor["name"]
                shaves = top_razor["shaves"]
                users = top_razor["unique_users"]
                observations.append(f"**{name}** led the razor category with ")
                observations.append(f"**{shaves} shaves** from **{users} users**.\n")

        # Top blades
        if "blades" in self.data and self.data["blades"]:
            top_blade = self.data["blades"][0]
            if "name" in top_blade and "shaves" in top_blade and "unique_users" in top_blade:
                name = top_blade["name"]
                shaves = top_blade["shaves"]
                users = top_blade["unique_users"]
                observations.append(f"**{name}** was the most popular blade with ")
                observations.append(f"**{shaves} shaves** from **{users} users**.\n")

        # Top brushes
        if "brushes" in self.data and self.data["brushes"]:
            top_brush = self.data["brushes"][0]
            if "name" in top_brush and "shaves" in top_brush and "unique_users" in top_brush:
                name = top_brush["name"]
                shaves = top_brush["shaves"]
                users = top_brush["unique_users"]
                observations.append(f"**{name}** topped the brush category with ")
                observations.append(f"**{shaves} shaves** from **{users} users**.\n")

        return observations

    def _generate_trend_analysis(self) -> List[str]:
        """Generate trend analysis based on comparison data."""
        observations = []

        if not self.comparison_data:
            return observations

        # Analyze format trends
        format_trends = self._analyze_format_trends()
        if format_trends:
            observations.append("### Format Trends\n")
            observations.extend(format_trends)
            observations.append("")

        # Analyze manufacturer trends
        manufacturer_trends = self._analyze_manufacturer_trends()
        if manufacturer_trends:
            observations.append("### Manufacturer Trends\n")
            observations.extend(manufacturer_trends)
            observations.append("")

        return observations

    def _analyze_format_trends(self) -> List[str]:
        """Analyze trends in razor formats."""
        observations = []

        if "razor_formats" not in self.data:
            return observations

        current_formats = {}
        for item in self.data["razor_formats"]:
            if "name" in item and "shaves" in item:
                current_formats[item["name"]] = item["shaves"]

        # Find the most popular format
        if current_formats:
            top_format = max(current_formats.items(), key=lambda x: x[1])
            observations.append(f"**{top_format[0]}** remains the dominant razor format with ")
            observations.append(f"**{top_format[1]:,} shaves** this month.\n")

        return observations

    def _analyze_manufacturer_trends(self) -> List[str]:
        """Analyze trends in manufacturer popularity."""
        observations = []

        if "razor_manufacturers" not in self.data:
            return observations

        current_manufacturers = {}
        for item in self.data["razor_manufacturers"]:
            if "name" in item and "shaves" in item:
                current_manufacturers[item["name"]] = item["shaves"]

        # Find the top manufacturer
        if current_manufacturers:
            top_manufacturer = max(current_manufacturers.items(), key=lambda x: x[1])
            observations.append(f"**{top_manufacturer[0]}** led razor manufacturers with ")
            observations.append(f"**{top_manufacturer[1]:,} shaves**.\n")

        return observations

    def _generate_format_insights(self) -> List[str]:
        """Generate insights about format distribution."""
        observations = []

        if "razor_formats" not in self.data:
            return observations

        formats = self.data["razor_formats"]
        total_razor_shaves = 0

        # Calculate total and filter valid items
        valid_formats = []
        for item in formats:
            if "name" in item and "shaves" in item:
                total_razor_shaves += item["shaves"]
                valid_formats.append(item)

        if total_razor_shaves == 0:
            return observations

        # Calculate format percentages
        format_percentages = []
        for item in valid_formats[:5]:  # Top 5 formats
            percentage = (item["shaves"] / total_razor_shaves) * 100
            format_percentages.append(f"{item['name']} ({percentage:.1f}%)")

        if format_percentages:
            observations.append("### Format Distribution\n")
            observations.append("The top razor formats by usage were: ")
            observations.append(", ".join(format_percentages) + ".\n")

        return observations

    def _generate_user_insights(self) -> List[str]:
        """Generate insights about user engagement."""
        observations = []

        # Analyze user participation
        total_shaves = self.metadata.get("total_shaves", 0)
        unique_shavers = self.metadata.get("unique_shavers", 0)

        if total_shaves > 0 and unique_shavers > 0:
            avg_shaves_per_user = total_shaves / unique_shavers
            observations.append("### User Engagement\n")

            if avg_shaves_per_user >= 15:
                observations.append(
                    "User engagement was **high** this month, with users averaging "
                )
                observations.append(f"**{avg_shaves_per_user:.1f} shaves** each.\n")
            elif avg_shaves_per_user >= 10:
                observations.append(
                    "User engagement was **moderate** this month, with users averaging "
                )
                observations.append(f"**{avg_shaves_per_user:.1f} shaves** each.\n")
            else:
                observations.append(
                    "User engagement was **lower** this month, with users averaging "
                )
                observations.append(f"**{avg_shaves_per_user:.1f} shaves** each.\n")

        return observations

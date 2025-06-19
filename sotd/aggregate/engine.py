"""Core aggregation engine using pandas for efficient data processing."""

from typing import Any, Dict, List

import pandas as pd

from sotd.aggregate.dataframe_utils import optimize_dataframe_operations, optimized_groupby_agg


def aggregate_razor_manufacturers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate razor usage statistics by manufacturer (brand).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        brand = matched.get("brand")
        if brand:
            data.append({"brand": brand, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for razor manufacturer aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during razor manufacturer aggregation: {e}")

    # Group by brand and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "brand", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group razor manufacturer data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during razor manufacturer grouping: {e}")

    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_blade_manufacturers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate blade usage statistics by manufacturer (brand).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        blade = record.get("blade", {})
        matched = blade.get("matched", {}) if isinstance(blade, dict) else {}
        brand = matched.get("brand")
        if brand:
            data.append({"brand": brand, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for blade manufacturer aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during blade manufacturer aggregation: {e}")

    # Group by brand and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "brand", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group blade manufacturer data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during blade manufacturer grouping: {e}")

    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_soap_makers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate soap usage statistics by maker (manufacturer).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        soap = record.get("soap", {})
        matched = soap.get("matched", {}) if isinstance(soap, dict) else {}
        maker = matched.get("maker")
        if maker:
            data.append({"maker": maker, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for soap maker aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during soap maker aggregation: {e}")

    # Group by maker and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "maker", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group soap maker data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during soap maker grouping: {e}")

    grouped.columns = ["maker", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_knot_makers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by knot maker (brand).
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {}) if isinstance(brush, dict) else {}
        brand = matched.get("brand")
        if brand:
            data.append({"brand": brand, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for brush knot maker aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush knot maker aggregation: {e}")

    # Group by brand and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "brand", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group brush knot maker data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush knot maker grouping: {e}")

    grouped.columns = ["brand", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_handle_makers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by handle maker.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {}) if isinstance(brush, dict) else {}
        handle_maker = matched.get("handle_maker")
        if handle_maker:
            data.append({"handle_maker": handle_maker, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for brush handle maker aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush handle maker aggregation: {e}")

    # Group by handle maker and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "handle_maker", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group brush handle maker data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush handle maker grouping: {e}")

    grouped.columns = ["handle_maker", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_fibers(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by fiber type.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {}) if isinstance(brush, dict) else {}
        fiber = matched.get("fiber")
        if fiber:
            data.append({"fiber": fiber, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for brush fiber aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush fiber aggregation: {e}")

    # Group by fiber and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "fiber", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group brush fiber data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush fiber grouping: {e}")

    grouped.columns = ["fiber", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_brush_knot_sizes(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate brush usage statistics by knot size.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        brush = record.get("brush", {})
        matched = brush.get("matched", {}) if isinstance(brush, dict) else {}
        knot_size = matched.get("knot_size_mm")
        if knot_size is not None:
            data.append({"knot_size_mm": str(knot_size), "user": record.get("author", "Unknown")})
    if not data:
        return []
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for brush knot size aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush knot size aggregation: {e}")
    try:
        grouped = optimized_groupby_agg(df, "knot_size_mm", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group brush knot size data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during brush knot size grouping: {e}")
    grouped.columns = ["knot_size_mm", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    # Ensure knot_size_mm is always a string in the output
    result = list(grouped.to_dict("records"))
    for r in result:
        r["knot_size_mm"] = str(r["knot_size_mm"])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_blackbird_plates(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Blackbird razor plate usage statistics.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        enriched = razor.get("enriched", {}) if isinstance(razor, dict) else {}

        # Check if this is a Blackbird razor
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        if "blackbird" in brand.lower() or "blackbird" in model.lower():
            plate = enriched.get("plate")
            if plate:
                data.append({"plate": plate, "user": record.get("author", "Unknown")})
    if not data:
        return []

    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for Blackbird plate aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Blackbird plate aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "plate", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group Blackbird plate data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Blackbird plate grouping: {e}")

    grouped.columns = ["plate", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_christopher_bradley_plates(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Christopher Bradley razor plate usage statistics.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        enriched = razor.get("enriched", {}) if isinstance(razor, dict) else {}

        # Check if this is a Christopher Bradley razor
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        if "karve" in brand.lower() and "christopher bradley" in model.lower():
            plate_level = enriched.get("plate_level")
            plate_type = enriched.get("plate_type", "SB")
            if plate_level:
                plate = f"{plate_level} {plate_type}"
                data.append({"plate": plate, "user": record.get("author", "Unknown")})
    if not data:
        return []

    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(
            f"Failed to create DataFrame for Christopher Bradley plate aggregation: {e}"
        )
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Christopher Bradley plate aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "plate", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group Christopher Bradley plate data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Christopher Bradley plate grouping: {e}")

    grouped.columns = ["plate", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_game_changer_plates(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Game Changer razor plate usage statistics.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        enriched = razor.get("enriched", {}) if isinstance(razor, dict) else {}

        # Check if this is a Game Changer razor
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        if "razorock" in brand.lower() and "game changer" in model.lower():
            gap = enriched.get("gap")
            variant = enriched.get("variant")
            plate = None
            if gap and variant:
                plate = f"Gap {gap} {variant}"
            elif gap:
                plate = f"Gap {gap}"
            elif variant:
                plate = variant
            if plate:
                data.append({"plate": plate, "user": record.get("author", "Unknown")})
    if not data:
        return []

    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for Game Changer plate aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Game Changer plate aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "plate", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group Game Changer plate data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Game Changer plate grouping: {e}")

    grouped.columns = ["plate", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_super_speed_tips(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate Super Speed razor tip usage statistics.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        enriched = razor.get("enriched", {}) if isinstance(razor, dict) else {}

        # Check if this is a Super Speed razor
        brand = matched.get("brand", "")
        model = matched.get("model", "")
        if "gillette" in brand.lower() and "super speed" in model.lower():
            tip = enriched.get("super_speed_tip")
            if tip:
                data.append({"tip": tip, "user": record.get("author", "Unknown")})
    if not data:
        return []

    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for Super Speed tip aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Super Speed tip aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "tip", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group Super Speed tip data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during Super Speed tip grouping: {e}")

    grouped.columns = ["tip", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_straight_razor_specs(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate straight razor specifications usage statistics.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        enriched = razor.get("enriched", {}) if isinstance(razor, dict) else {}

        # Check if this is a straight razor
        format_type = matched.get("format", "")
        if "straight" in format_type.lower():
            grind = enriched.get("grind")
            width = enriched.get("width")
            point = enriched.get("point")
            spec_parts = []
            if grind:
                spec_parts.append(f"Grind: {grind}")
            if width:
                spec_parts.append(f"Width: {width}")
            if point:
                spec_parts.append(f"Point: {point}")
            if spec_parts:
                specs = " | ".join(spec_parts)
                data.append({"specs": specs, "user": record.get("author", "Unknown")})
    if not data:
        return []

    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for straight razor spec aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during straight razor spec aggregation: {e}")

    try:
        grouped = optimized_groupby_agg(df, "specs", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group straight razor spec data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during straight razor spec grouping: {e}")

    grouped.columns = ["specs", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore


def aggregate_razor_blade_combinations(
    records: List[Dict[str, Any]], debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Aggregate razor-blade combination usage statistics.
    """
    if not isinstance(records, list):
        raise ValueError(f"Expected list of records, got {type(records)}")
    if not records:
        return []
    data = []
    for record in records:
        razor = record.get("razor", {})
        blade = record.get("blade", {})
        razor_matched = razor.get("matched", {}) if isinstance(razor, dict) else {}
        blade_matched = blade.get("matched", {}) if isinstance(blade, dict) else {}

        razor_brand = razor_matched.get("brand", "")
        razor_model = razor_matched.get("model", "")
        blade_brand = blade_matched.get("brand", "")
        blade_model = blade_matched.get("model", "")

        if razor_brand and razor_model and blade_brand and blade_model:
            razor_name = f"{razor_brand} {razor_model}".strip()
            blade_name = f"{blade_brand} {blade_model}".strip()
            combination = f"{razor_name} + {blade_name}"
            data.append({"combination": combination, "user": record.get("author", "Unknown")})
    if not data:
        return []

    # Convert to DataFrame for aggregation
    try:
        df = pd.DataFrame(data)
        df = optimize_dataframe_operations(df, debug)
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError(f"Failed to create DataFrame for razor-blade combination aggregation: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during razor-blade combination aggregation: {e}")

    # Group by combination and calculate metrics
    try:
        grouped = optimized_groupby_agg(df, "combination", "user", ["count", "nunique"], debug)
    except (KeyError, ValueError) as e:
        raise ValueError(f"Failed to group razor-blade combination data: {e}")
    except ImportError as e:
        raise RuntimeError(f"Pandas import error during razor-blade combination grouping: {e}")

    grouped.columns = ["combination", "shaves", "unique_users"]
    grouped["avg_shaves_per_user"] = (grouped["shaves"] / grouped["unique_users"]).round(2)
    grouped = grouped.sort_values(["shaves", "unique_users"], ascending=[False, False])
    return list(grouped.to_dict("records"))  # type: ignore

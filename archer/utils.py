from datetime import datetime, timedelta, timezone


def get_formatted_times(user_timezone: str | None = None) -> str:
    """
    Returns a formatted string with current times in major time zones.

    This helps the LLM provide accurate time-based information regardless of user location.
    Includes UTC, Eastern Time (ET), Central Time (CT), Pacific Time (PT), and GMT.
    """
    # Get current UTC time
    utc_now = datetime.now(timezone.utc)

    # Define major time zone offsets (hours from UTC)
    time_zones = {
        "UTC": 0,
        "Eastern Time (ET)": -5,  # EST is UTC-5, EDT is UTC-4
        "Central Time (CT)": -6,  # CST is UTC-6, CDT is UTC-5
        "Mountain Time (MT)": -7,  # MST is UTC-7, MDT is UTC-6
        "Pacific Time (PT)": -8,  # PST is UTC-8, PDT is UTC-7
        "GMT": 0,
        "Central European Time (CET)": 1,  # CET is UTC+1, CEST is UTC+2
        "Japan Standard Time (JST)": 9,  # UTC+9
        "Australian Eastern Time (AET)": 10,  # AEST is UTC+10, AEDT is UTC+11
    }

    # Simple DST adjustment (March-November for US time zones)
    # This is a simplified approach and doesn't account for exact DST transition dates
    is_dst_us = 3 <= utc_now.month <= 11
    is_dst_eu = 3 <= utc_now.month <= 10
    is_dst_au = utc_now.month <= 4 or utc_now.month >= 10  # Southern hemisphere DST

    # Apply DST adjustments
    if is_dst_us:
        time_zones["Eastern Time (ET)"] += 1
        time_zones["Central Time (CT)"] += 1
        time_zones["Mountain Time (MT)"] += 1
        time_zones["Pacific Time (PT)"] += 1

    if is_dst_eu:
        time_zones["Central European Time (CET)"] += 1

    if is_dst_au:
        time_zones["Australian Eastern Time (AET)"] += 1

    # Format the time string
    time_strings = []
    date_format = "%Y-%m-%d"
    time_format = "%H:%M:%S"

    for zone_name, offset in time_zones.items():
        zone_time = utc_now.replace(tzinfo=timezone(timedelta(hours=offset)))
        time_strings.append(f"{zone_name}: {zone_time.strftime(f'{date_format} {time_format}')}")

    # TODO: Add user timezone to the time strings
    # if user_timezone:
    #    time_strings.append(f"User timezone: {user_timezone}")

    return "\n".join(time_strings)


def get_tool_section(
    tool_descriptions: dict[str, str] | None,
    shorten_descriptions: bool = True,
) -> str:
    """
    Generates and returns a formatted tools section string from the provided tool descriptions.

    If shorten_descriptions is True, only the content up to the first newline of each
    tool's description is used.

    Args:
        tool_descriptions: A dictionary mapping tool names to their descriptions.
        shorten_descriptions: Whether to keep only the first line of each description.

    Returns:
        A formatted string listing each tool and its (optionally shortened) description.
    """
    if not tool_descriptions or len(tool_descriptions) == 0:
        return ""

    tools_section = "Available tools:\n"

    for tool_name, description in tool_descriptions.items():
        if shorten_descriptions:
            # Use only the first line of the description
            # (even if there are none this returns the full string)
            first_line = description.split("\n")[0]
            tools_section += f"- {tool_name}: {first_line}\n"
        else:
            tools_section += f"- {tool_name}: {description}\n"

    return tools_section

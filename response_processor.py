import re
import json
from typing import Dict, List, Any
from datetime import datetime


class ResponseProcessor:
    """Process agent responses to extract clean answers with data"""

    @staticmethod
    def extract_numeric_data(tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract numeric data from tool results"""
        data = {
            "amounts": [],
            "totals": [],
            "categories": {},
            "merchants": {},
            "dates": [],
        }

        for result in tool_results:
            if isinstance(result.get("content"), str):
                try:
                    parsed = json.loads(result["content"])

                    # Extract total_spent
                    if "total_spent" in parsed:
                        data["totals"].append(
                            {
                                "value": parsed["total_spent"],
                                "context": result.get("tool_name", "unknown"),
                                "args": result.get("args", {}),
                            }
                        )

                    # Extract category data
                    if "spending_by_category" in parsed:
                        data["categories"].update(parsed["spending_by_category"])

                    # Extract merchant data
                    if "top_merchants" in parsed:
                        data["merchants"].update(parsed["top_merchants"])

                except json.JSONDecodeError:
                    pass

        return data

    @staticmethod
    def format_comparative_response(query: str, data: Dict[str, Any]) -> str:
        """Format response for comparative queries"""
        totals = data.get("totals", [])

        if len(totals) < 2:
            return "Insufficient data for comparison."

        # Check if this is a time-based comparison
        is_time_comparison = any(
            keyword in query.lower()
            for keyword in ["increase", "decrease", "from", "to", "vs", "versus"]
        )

        if is_time_comparison:
            # Sort by date if available
            sorted_totals = sorted(
                totals, key=lambda x: x.get("args", {}).get("start_date", "")
            )

            if len(sorted_totals) >= 2:
                first = sorted_totals[0]
                second = sorted_totals[1]

                diff = second["value"] - first["value"]
                percent_change = (
                    (diff / first["value"] * 100) if first["value"] != 0 else 0
                )

                # Format periods
                first_period = ResponseProcessor._format_period(first.get("args", {}))
                second_period = ResponseProcessor._format_period(second.get("args", {}))

                result = f"{first_period}: ${first['value']:.2f}\n"
                result += f"{second_period}: ${second['value']:.2f}\n\n"

                if diff > 0:
                    result += f"The spending increased by ${abs(diff):.2f} ({percent_change:.1f}%)."
                elif diff < 0:
                    result += f"The spending decreased by ${abs(diff):.2f} ({abs(percent_change):.1f}%)."
                else:
                    result += "The spending remained the same."

                return result

        # Category comparison
        if len(totals) == 2:
            first = totals[0]
            second = totals[1]

            first_name = first.get("args", {}).get("category", "First")
            second_name = second.get("args", {}).get("category", "Second")

            result = f"{first_name.title()}: ${first['value']:.2f}\n"
            result += f"{second_name.title()}: ${second['value']:.2f}\n\n"

            if first["value"] > second["value"]:
                diff = first["value"] - second["value"]
                result += (
                    f"You spent ${diff:.2f} more on {first_name} than {second_name}."
                )
            elif second["value"] > first["value"]:
                diff = second["value"] - first["value"]
                result += (
                    f"You spent ${diff:.2f} more on {second_name} than {first_name}."
                )
            else:
                result += f"You spent the same amount on both categories."

            return result

        return "Unable to format comparison."

    @staticmethod
    def _format_period(args: Dict) -> str:
        """Format date range into readable period"""
        start_date = args.get("start_date", "")
        end_date = args.get("end_date", "")
        category = args.get("category", "")

        if start_date and end_date:
            # Extract month/year
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")

                if start.month == end.month and start.year == end.year:
                    period = start.strftime("%B %Y")
                else:
                    period = f"{start.strftime('%B %Y')} to {end.strftime('%B %Y')}"

                if category:
                    return f"{category.title()} ({period})"
                return period
            except:
                pass

        if category:
            return category.title()

        return "Period"

    @staticmethod
    def should_use_comparative_format(query: str, tool_results: List[Dict]) -> bool:
        """Determine if query needs comparative formatting"""
        comparative_keywords = [
            "more",
            "less",
            "vs",
            "versus",
            "compare",
            "increase",
            "decrease",
            "higher",
            "lower",
            "from",
            "to",
            "than",
        ]

        has_comparative_keyword = any(
            kw in query.lower() for kw in comparative_keywords
        )
        has_multiple_results = len(tool_results) >= 2

        return has_comparative_keyword and has_multiple_results

    @staticmethod
    def process_response(
        query: str, response: str, tool_results: List[Dict[str, Any]]
    ) -> str:
        """Main processing function"""

        # Extract numeric data from tool results
        data = ResponseProcessor.extract_numeric_data(tool_results)

        # Check if we should use comparative format
        if ResponseProcessor.should_use_comparative_format(query, tool_results):
            formatted = ResponseProcessor.format_comparative_response(query, data)
            if formatted and len(formatted) > 20:
                return formatted

        # Otherwise, clean up the response
        # Remove technical jargon
        clean = re.sub(
            r"(Based on the tool call responses?|The tool returned|Assuming)",
            "",
            response,
            flags=re.IGNORECASE,
        )

        # Remove JSON artifacts
        clean = re.sub(r'\{[^}]*"name"[^}]*\}', "", clean)

        # Clean whitespace
        clean = re.sub(r"\n\s*\n\s*\n+", "\n\n", clean)
        clean = clean.strip()

        return clean if len(clean) > 20 else response

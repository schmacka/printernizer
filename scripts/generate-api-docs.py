#!/usr/bin/env python3
"""
Generate API documentation from FastAPI OpenAPI specification.

This script extracts the OpenAPI JSON from the running Printernizer API
and converts it to markdown format for MkDocs documentation.

Usage:
    python scripts/generate-api-docs.py
    python scripts/generate-api-docs.py --url http://localhost:8000
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import requests


def fetch_openapi_spec(base_url: str) -> Dict[str, Any]:
    """Fetch OpenAPI specification from the API."""
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching OpenAPI spec: {e}")
        print(f"Make sure Printernizer is running at {base_url}")
        sys.exit(1)


def group_endpoints_by_tag(spec: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Group API endpoints by their tags."""
    endpoints_by_tag = {}

    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                tags = details.get("tags", ["Untagged"])
                for tag in tags:
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    endpoints_by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "details": details
                    })

    return endpoints_by_tag


def format_method_badge(method: str) -> str:
    """Format HTTP method as a colored badge."""
    colors = {
        "GET": "blue",
        "POST": "green",
        "PUT": "orange",
        "PATCH": "purple",
        "DELETE": "red"
    }
    color = colors.get(method, "gray")
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 3px; font-weight: bold;">{method}</span>'


def format_schema_type(schema: Dict[str, Any]) -> str:
    """Format schema type for display."""
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return ref_name
    if "type" in schema:
        return schema["type"]
    if "allOf" in schema:
        return "object"
    return "any"


def format_parameter(param: Dict[str, Any]) -> str:
    """Format a parameter for display."""
    name = param.get("name", "")
    required = "**required**" if param.get("required", False) else "optional"
    param_type = param.get("schema", {}).get("type", "string")
    description = param.get("description", "")

    return f"- `{name}` ({param_type}, {required}) - {description}"


def format_request_body(body: Dict[str, Any], components: Dict[str, Any]) -> str:
    """Format request body schema."""
    if "content" not in body:
        return ""

    content = body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return f"Request body schema: `{ref_name}`\n\nSee [Models](#models) section for details."

    return "Request body: JSON object"


def format_response(status_code: str, response: Dict[str, Any]) -> str:
    """Format a response for display."""
    description = response.get("description", "")
    content = response.get("content", {})

    output = f"**{status_code}**: {description}\n\n"

    if content:
        json_content = content.get("application/json", {})
        if json_content:
            schema = json_content.get("schema", {})
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                output += f"Response schema: `{ref_name}`\n"

    return output


def generate_endpoint_doc(endpoint: Dict[str, Any], components: Dict[str, Any]) -> str:
    """Generate markdown documentation for a single endpoint."""
    path = endpoint["path"]
    method = endpoint["method"]
    details = endpoint["details"]

    # Header
    output = f"### {format_method_badge(method)} `{path}`\n\n"

    # Summary and description
    summary = details.get("summary", "")
    description = details.get("description", "")

    if summary:
        output += f"**{summary}**\n\n"
    if description:
        output += f"{description}\n\n"

    # Parameters
    parameters = details.get("parameters", [])
    if parameters:
        output += "**Parameters:**\n\n"
        for param in parameters:
            output += format_parameter(param) + "\n"
        output += "\n"

    # Request body
    request_body = details.get("requestBody", {})
    if request_body:
        output += "**Request Body:**\n\n"
        output += format_request_body(request_body, components) + "\n\n"

    # Responses
    responses = details.get("responses", {})
    if responses:
        output += "**Responses:**\n\n"
        for status_code, response in responses.items():
            output += format_response(status_code, response) + "\n"

    output += "---\n\n"
    return output


def generate_tag_doc(tag: str, endpoints: List[Dict[str, Any]], spec: Dict[str, Any]) -> str:
    """Generate markdown documentation for a tag (router)."""
    components = spec.get("components", {})

    # Header
    output = f"# {tag} API\n\n"

    # Tag description (if available)
    tag_descriptions = {t["name"]: t.get("description", "") for t in spec.get("tags", [])}
    if tag in tag_descriptions and tag_descriptions[tag]:
        output += f"{tag_descriptions[tag]}\n\n"

    # Base URL
    servers = spec.get("servers", [{"url": "http://localhost:8000"}])
    base_url = servers[0]["url"] if servers else "http://localhost:8000"
    output += f"**Base URL:** `{base_url}`\n\n"

    # Endpoints
    output += "## Endpoints\n\n"

    # Sort endpoints by path and method
    sorted_endpoints = sorted(endpoints, key=lambda e: (e["path"], e["method"]))

    for endpoint in sorted_endpoints:
        output += generate_endpoint_doc(endpoint, components)

    # Models (schemas) used by this tag
    output += generate_models_section(tag, endpoints, components)

    return output


def generate_models_section(tag: str, endpoints: List[Dict[str, Any]], components: Dict[str, Any]) -> str:
    """Generate models/schemas section for a tag."""
    # Collect all referenced schemas
    schemas = components.get("schemas", {})
    if not schemas:
        return ""

    output = "## Models\n\n"
    output += "API request and response schemas.\n\n"

    # For now, just list the available schemas
    # In the future, this could be expanded to show full schema details
    for schema_name, schema_def in schemas.items():
        output += f"### {schema_name}\n\n"

        description = schema_def.get("description", "")
        if description:
            output += f"{description}\n\n"

        properties = schema_def.get("properties", {})
        if properties:
            output += "**Properties:**\n\n"
            for prop_name, prop_def in properties.items():
                prop_type = format_schema_type(prop_def)
                prop_desc = prop_def.get("description", "")
                required = "required" if prop_name in schema_def.get("required", []) else "optional"
                output += f"- `{prop_name}` ({prop_type}, {required})"
                if prop_desc:
                    output += f" - {prop_desc}"
                output += "\n"

        output += "\n"

    return output


def main():
    """Main function to generate API documentation."""
    parser = argparse.ArgumentParser(description="Generate API documentation from OpenAPI spec")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the Printernizer API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--output-dir",
        default="docs/api-reference",
        help="Output directory for generated docs (default: docs/api-reference)"
    )
    args = parser.parse_args()

    print(f"Fetching OpenAPI specification from {args.url}...")
    spec = fetch_openapi_spec(args.url)

    print("Grouping endpoints by tag...")
    endpoints_by_tag = group_endpoints_by_tag(spec)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating documentation files in {output_dir}...")

    # Generate a file for each tag
    tag_mapping = {
        "printers": "printers.md",
        "jobs": "jobs.md",
        "files": "files.md",
        "analytics": "analytics.md",
        "websocket": "websocket.md",
        "settings": "settings.md",
        "system": "system.md",
        "health": "health.md",
        "camera": "camera.md",
        "materials": "materials.md",
        "library": "library.md",
        "ideas": "ideas.md",
        "timelapses": "timelapses.md",
        "trending": "trending.md",
        "search": "search.md",
    }

    for tag, endpoints in endpoints_by_tag.items():
        # Map tag name to filename
        filename = tag_mapping.get(tag.lower(), f"{tag.lower().replace(' ', '-')}.md")
        filepath = output_dir / filename

        print(f"  - Generating {filename} ({len(endpoints)} endpoints)")

        doc_content = generate_tag_doc(tag, endpoints, spec)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(doc_content)

    print(f"\n✅ Successfully generated API documentation!")
    print(f"   Output: {output_dir}")
    print(f"   Files created: {len(endpoints_by_tag)}")
    print(f"\nNext steps:")
    print(f"  1. Review generated files in {output_dir}")
    print(f"  2. Run 'mkdocs serve' to preview documentation")
    print(f"  3. Customize generated docs if needed")


if __name__ == "__main__":
    main()

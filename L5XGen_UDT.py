#L5XGen_UDT.py
import datetime
import re

# Priority map for sorting members by type and whether array or not
TYPE_PRIORITY = {
    "BOOL": 0,
    "BOOL_ARRAY": 1,
    "SINT": 2,
    "SINT_ARRAY": 3,
    "INT": 4,
    "INT_ARRAY": 5,
    "DINT": 6,
    "DINT_ARRAY": 7,
    "REAL": 8,
    "REAL_ARRAY": 9,
    "STRING": 10,
    "STRING_ARRAY": 11,
    "TIMER": 12,
    "COUNTER": 13,
    "OTHER": 14
}

SUPPORTED_TYPES = {"BOOL", "SINT", "INT", "DINT", "REAL", "STRING", "TIMER", "COUNTER"}

def sanitize_name(name: str) -> str:
    """Sanitize tag or UDT name to valid identifier format."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name.strip())

def get_type_priority(tag_type: str, dimension: int) -> int:
    """Get priority for sorting based on base type and dimension (array or scalar)."""
    tag_type = tag_type.upper()
    if dimension > 0:
        if tag_type == "REAL":
            key = "REAL_ARRAY"
        elif tag_type == "STRING":
            key = "STRING_ARRAY"
        elif tag_type == "BOOL":
            key = "BOOL_ARRAY"
        else:
            key = f"{tag_type}_ARRAY"
    else:
        key = tag_type
    return TYPE_PRIORITY.get(key, TYPE_PRIORITY["OTHER"])

def format_description(description: str) -> str:
    """Format description into XML CDATA block if present."""
    if description:
        return f"\n          <Description>\n            <![CDATA[{description}]]>\n          </Description>"
    return ""

def generate_udt_l5x_from_tags(data_dict, controller_name="Controller") -> dict:
    """
    Generate a ControlLogix L5X UDT definition XML from tags dictionary.
    Input: data_dict with keys:
      - udt_name: str
      - tags: list of dicts with 'name', 'type', optional 'description', 'external_access', 'hidden'
    Returns dict with success flag, UDT XML string, filename, and message.
    """
    if not isinstance(data_dict, dict):
        return {"success": False, "error": "Input must be a dictionary."}

    tag_list = data_dict.get("tags", [])
    udt_name = sanitize_name(data_dict.get("udt_name", "GeneratedUDT"))

    if not isinstance(tag_list, list) or not tag_list:
        return {"success": False, "error": "No tags provided."}

    try:
        now = datetime.datetime.utcnow().strftime('%a %b %d %H:%M:%S %Y')
        cleaned_tags = []

        for tag in tag_list:
            raw_type = str(tag.get("type", "")).strip().upper()
            match = re.match(r"(\w+)(?:\[(\d*)\])?", raw_type)
            if not match:
                # Skip tags with invalid type format
                continue

            base_type, size = match.groups()
            base_type = base_type.upper()
            if base_type not in SUPPORTED_TYPES:
                # Skip unsupported types
                continue

            # Handle dimension parsing
            if size is None:
                dimension = 0
            elif size == "":
                # Empty brackets e.g. INT[] treated as dimension 1
                dimension = 1
            else:
                try:
                    dimension = int(size)
                    if dimension < 0:
                        # Negative dimension invalid, skip
                        continue
                except ValueError:
                    # Invalid dimension, skip tag
                    continue

            # Validate BOOL array dimension: 0 or multiple of 32 only
            if base_type == "BOOL" and dimension not in (0,) + tuple(range(32, 1025, 32)):
                # Disallow e.g. BOOL[10], only allow 32,64,96,... up to 1024 max
                continue

            # Sanitize tag name
            name = sanitize_name(str(tag.get("name", "")).strip())
            if not name:
                # Skip tags without valid names
                continue

            description = str(tag.get("description", name))

            external_access = tag.get("external_access", "Read/Write")
            hidden = tag.get("hidden", False)

            cleaned_tags.append({
                "name": name,
                "type": base_type,
                "dimension": dimension,
                "description": description,
                "external_access": external_access,
                "hidden": hidden
            })

        if not cleaned_tags:
            return {"success": False, "error": "No valid or supported tags found after processing."}

        # Sort tags by type priority and name
        sorted_tags = sorted(cleaned_tags, key=lambda t: (get_type_priority(t["type"], t["dimension"]), t["name"].lower()))

        l5x_members = []
        bool_pack = []

        def flush_bool_pack():
            """Flush accumulated BOOL bits into a packed SINT and BIT members."""
            nonlocal l5x_members, bool_pack
            if not bool_pack:
                return
            first_bool_name = bool_pack[0]['name']
            hidden_sint_name = f"ZZZZZZZZZZ{first_bool_name}"
            # Add hidden SINT to hold bits
            l5x_members.append(
                f'''          <Member Name="{hidden_sint_name}" DataType="SINT" Dimension="0" Radix="Decimal" Hidden="true" ExternalAccess="Read/Write"/>'''
            )
            # Add bit members referencing the hidden SINT bits
            for bit_index, tag in enumerate(bool_pack):
                desc_block = format_description(tag["description"])
                external_access = tag.get("external_access", "Read/Write")
                l5x_members.append(
                    f'''          <Member Name="{tag['name']}" DataType="BIT" Dimension="0" Radix="Decimal" Hidden="false" Target="{hidden_sint_name}" BitNumber="{bit_index}" ExternalAccess="{external_access}">{desc_block}
          </Member>'''
                )
            bool_pack.clear()

        # Build members XML
        for tag in sorted_tags:
            dtype = tag["type"]
            dimension = tag["dimension"]

            if dtype == "BOOL" and dimension == 0:
                # Bit-pack individual BOOL tags into SINT packs of 8 bits
                bool_pack.append(tag)
                if len(bool_pack) == 8:
                    flush_bool_pack()
            else:
                # Flush any pending bool pack before adding non-BOOL or arrays
                flush_bool_pack()

                desc_block = format_description(tag["description"])

                # Radix only Decimal for integral types and BOOL, else NullType
                if dtype in ["BOOL", "SINT", "INT", "DINT"]:
                    radix = "Decimal"
                else:
                    radix = "NullType"

                l5x_members.append(
                    f'''          <Member Name="{tag['name']}" DataType="{dtype}" Dimension="{dimension}" Radix="{radix}" Hidden="{str(tag.get("hidden", False)).lower()}" ExternalAccess="{tag.get("external_access", "Read/Write")}">{desc_block}
          </Member>'''
                )

        # Flush remaining BOOL bit pack if any
        flush_bool_pack()

        # Compose final L5X XML string
        udt_l5x = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="32.04" TargetName="{udt_name}" TargetType="DataType" ContainsContext="true" ExportDate="{now}" ExportOptions="References NoRawData L5KData DecoratedData Context Dependencies ForceProtectedEncoding AllProjDocTrans">
  <Controller Use="Context" Name="{controller_name}">
    <DataTypes Use="Context">
      <DataType Use="Target" Name="{udt_name}" Family="NoFamily" Class="User">
        <Members>
{chr(10).join(l5x_members)}
        </Members>
      </DataType>
    </DataTypes>
  </Controller>
</RSLogix5000Content>"""

        return {
            "success": True,
            "udt_text": udt_l5x,
            "download_name": f"{udt_name}.l5x",
            "message": f"UDT '{udt_name}' generated successfully with BOOL bit-packing."
        }

    except Exception as e:
        return {"success": False, "error": f"Exception during UDT generation: {str(e)}"}

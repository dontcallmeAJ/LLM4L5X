# L5X_UDTVerify.py
import xml.etree.ElementTree as ET
import os
from collections import defaultdict

DATA_TYPE_ORDER = [
    'BOOL_SINGLE', 'BOOL_ARRAY', 'SINT', 'INT', 'DINT',
    'SINT_ARRAY', 'INT_ARRAY', 'DINT_ARRAY', 'REAL', 'REAL_ARRAY',
    'STRING', 'TIMER', 'OTHER'
]

def classify_member(member):
    dtype = member.attrib.get('DataType')
    dim = int(member.attrib.get('Dimension', '0'))
    if dtype == 'BIT':
        return 'BOOL_SINGLE'
    if dtype == 'BOOL':
        return 'BOOL_ARRAY' if dim > 0 else 'BOOL_SINGLE'
    if dtype == 'SINT':
        return 'SINT_ARRAY' if dim > 0 else 'SINT'
    if dtype == 'INT':
        return 'INT_ARRAY' if dim > 0 else 'INT'
    if dtype == 'DINT':
        return 'DINT_ARRAY' if dim > 0 else 'DINT'
    if dtype == 'REAL':
        return 'REAL_ARRAY' if dim > 0 else 'REAL'
    if dtype == 'STRING':
        return 'STRING'
    if dtype == 'TIMER':
        return 'TIMER'
    return 'OTHER'

def reorder_members(members):
    grouped = defaultdict(list)
    for m in members:
        if m.attrib.get('Hidden', 'false') == 'true':
            continue
        grouped[classify_member(m)].append(m)
    for group in grouped.values():
        group.sort(key=lambda x: x.attrib['Name'])
    reordered = []
    for dt in DATA_TYPE_ORDER:
        reordered.extend(grouped.get(dt, []))
    return reordered

def _get_udt_optimization_status(input_path):
    try:
        tree = ET.parse(input_path)
        root = tree.getroot()
        members_container = root.find('.//DataType/Members')
        if members_container is None:
            return False, "No UDT members found. No changes needed."

        original_members = list(members_container)
        reordered_members = reorder_members(original_members)

        orig_names = [m.attrib['Name'] for m in original_members if m.attrib.get('Hidden', 'false') != 'true']
        reordered_names = [m.attrib['Name'] for m in reordered_members]

        if len(orig_names) != len(reordered_names) or any(o != r for o, r in zip(orig_names, reordered_names)):
            return True, "UDT members are unoptimized. Sorting is recommended."
        return False, "UDT is already optimized. No sorting needed."
    except ET.ParseError as e:
        print(f"Parse error: {e}")
        return False, f"Error parsing L5X file: {e}"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, f"An unexpected error occurred: {e}"

def check_l5x_udt_optimization(input_path):
    needs_opt, msg = _get_udt_optimization_status(input_path)
    return {"success": True, "needs_optimization": needs_opt, "message": msg}

def process_l5x_udt_verification(input_path, output_path):
    try:
        needs_opt, msg = _get_udt_optimization_status(input_path)
        if not needs_opt:
            print(f"UDT already optimized: {input_path}")
            return {"success": True, "download_name": os.path.basename(input_path), "message": msg, "send_file": False}

        tree = ET.parse(input_path)
        root = tree.getroot()
        members_container = root.find('.//DataType/Members')
        if members_container is None:
            print(f"No members found in {input_path} during processing.")
            return {"success": True, "download_name": os.path.basename(input_path), "message": "No UDT members found. No changes performed.", "send_file": False}

        original_members = list(members_container)
        reordered_members = reorder_members(original_members)

        # Remove visible members and append reordered
        for m in list(members_container):
            if m.attrib.get('Hidden', 'false') != 'true':
                members_container.remove(m)
        for m in reordered_members:
            members_container.append(m)
        # Append hidden members at the end (preserving order)
        for m in original_members:
            if m.attrib.get('Hidden', 'false') == 'true' and m not in members_container:
                members_container.append(m)

        ET.indent(tree, space="  ", level=0)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"UDT reordered and saved: {output_path}")
        return {"success": True, "download_name": "UDTSorted.l5x", "message": "UDT members successfully reordered and optimized. Download will begin shortly.", "send_file": True}

    except ET.ParseError as e:
        print(f"Parse error: {e}")
        raise ValueError(f"Invalid L5X file: {e}")
    except Exception as e:
        print(f"Processing error: {e}")
        raise

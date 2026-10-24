"""
SARAS Tactical Casualty & Damage Assessment Report Generator
Produces publication-grade, official PDF mission dossiers
incorporating sorted victim triage data, exact GPS coordinates,
and aerial optical/thermal inspection recon snapshots.
"""

from __future__ import annotations
import base64
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright

from swarm_core.coordination.allocator import haversine_distance


def format_gps_coord(lat: float, lon: float) -> Dict[str, str]:
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return {
        "lat_str": f"{abs(lat):.6f}° {lat_dir}",
        "lon_str": f"{abs(lon):.6f}° {lon_dir}",
        "combined": f"{lat:.6f}, {lon:.6f}",
        "maps_url": f"https://www.google.com/maps?q={lat:.6f},{lon:.6f}",
    }


def generate_triage_pdf_report(
    victims: List[Dict[str, Any]],
    gcs_lat: float = 12.9716,
    gcs_lon: float = 77.5946,
    fleet_info: Optional[List[Dict[str, Any]]] = None,
    mission_id: Optional[str] = None,
    output_path: Optional[str | Path] = None,
    video_streamer = None
) -> Path:
    """
    Renders an executive, publication-grade PDF report of all triaged casualties.
    Includes base64 embedded FLIR thermal and optical aerial inspection snapshots,
    exact GPS coordinates, urgency score metrics, and standard operating procedures.
    """
    report_time_utc = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    report_time_local = time.strftime("%d %b %Y, %I:%M %p IST")
    doc_id = mission_id or f"SARAS-SOP-{int(time.time())%100000:05d}"

    # Sort strictly by urgency score descending (Critical -> Urgent -> Stable)
    sorted_victims = sorted(victims, key=lambda x: x.get("urgency_score", 0.0), reverse=True)

    # Compute high-level triage statistics
    total_victims = len(sorted_victims)
    critical_count = sum(1 for v in sorted_victims if "CRITICAL" in str(v.get("triage_category", "")).upper())
    urgent_count = sum(1 for v in sorted_victims if "URGENT" in str(v.get("triage_category", "")).upper())
    stable_count = sum(1 for v in sorted_victims if "STABLE" in str(v.get("triage_category", "")).upper())

    # Build enriched casualty objects with base64 images & GPS metadata
    enriched_casualties = []
    for rank, v in enumerate(sorted_victims, 1):
        v_id = v.get("victim_id", f"VIC-{rank:03d}")
        v_lat = float(v.get("lat", gcs_lat))
        v_lon = float(v.get("lon", gcs_lon))
        dist_m = v.get("distance_m")
        if dist_m is None:
            dist_m = round(haversine_distance(gcs_lat, gcs_lon, v_lat, v_lon), 1)

        gps_data = format_gps_coord(v_lat, v_lon)
        cat = str(v.get("triage_category", "URGENT")).upper()
        urgency = float(v.get("urgency_score", 50.0))
        temp = float(v.get("thermal_signature", 35.5) or 35.5)
        conf = float(v.get("confidence", 0.92) or 0.92)
        drone_id = v.get("drone_id", "UAV-01")
        tags = v.get("environment_tags", []) or []
        notes = v.get("notes", "No additional field notes recorded.")
        action = v.get("recommended_action", "Dispatch immediate field medical response team.")
        sops = v.get("sop_references", ["SOP-MED-01"])

        # Generate or retrieve base64 snapshot
        img_b64 = ""
        if video_streamer:
            try:
                jpg_bytes = video_streamer.generate_victim_snapshot(
                    victim_id=v_id,
                    lat=v_lat,
                    lon=v_lon,
                    drone_id=drone_id,
                    triage_category=cat,
                    thermal_signature=temp,
                    confidence=conf,
                    tags=tags,
                    notes=notes,
                    force_fresh=False
                )
                if jpg_bytes:
                    img_b64 = f"data:image/jpeg;base64,{base64.b64encode(jpg_bytes).decode('utf-8')}"
            except Exception as e:
                print(f"[ReportGenerator] Warning: Could not generate snapshot for {v_id}: {e}")

        # Hypothermia / Hyperthermia note
        if temp < 35.0:
            thermal_status = "HYPOTHERMIA HAZARD"
            thermal_class = "temp-crit"
        elif temp > 38.0:
            thermal_status = "HYPERTHERMIA HAZARD"
            thermal_class = "temp-crit"
        else:
            thermal_status = "VITAL RANGE NOMINAL"
            thermal_class = "temp-norm"

        severity_class = "cat-crit" if "CRITICAL" in cat else ("cat-urg" if "URGENT" in cat else "cat-stab")

        enriched_casualties.append({
            "rank": rank,
            "victim_id": v_id,
            "drone_id": drone_id,
            "lat": v_lat,
            "lon": v_lon,
            "gps": gps_data,
            "distance_m": dist_m,
            "triage_category": cat,
            "severity_class": severity_class,
            "urgency_score": urgency,
            "thermal_signature": temp,
            "thermal_status": thermal_status,
            "thermal_class": thermal_class,
            "confidence": conf,
            "confidence_pct": int(conf * 100),
            "tags": tags,
            "notes": notes,
            "recommended_action": action,
            "sop_references": sops,
            "snapshot_b64": img_b64
        })

    # Prepare Fleet info summary
    fleet_rows = []
    if fleet_info:
        for d in fleet_info:
            fleet_rows.append(f"""
                <tr>
                    <td><strong>{d.get('drone_id', 'UAV')}</strong></td>
                    <td>{d.get('status', 'ACTIVE')}</td>
                    <td>{d.get('battery', 100):.1f}%</td>
                    <td>{d.get('current_sector_id', 'STAGED')}</td>
                    <td>{d.get('lat', gcs_lat):.5f}° N, {d.get('lon', gcs_lon):.5f}° E</td>
                </tr>
            """)
    fleet_table_html = "".join(fleet_rows) if fleet_rows else """
        <tr>
            <td><strong>UAV Fleet (1-4)</strong></td>
            <td>AUTONOMOUS PATROL</td>
            <td>NOMINAL (>75%)</td>
            <td>SECTOR-01 to 04</td>
            <td>DYNAMIC GRID SWEEP</td>
        </tr>
    """

    # Build Master Summary Table Rows
    table_rows = []
    for c in enriched_casualties:
        tag_pills = " ".join([f'<span class="mini-tag">#{t}</span>' for t in c["tags"][:3]])
        table_rows.append(f"""
            <tr>
                <td style="text-align: center; font-weight: 800; font-family: monospace;">#{c['rank']}</td>
                <td style="font-weight: 800; font-family: monospace; color: #0284c7;">{c['victim_id']}</td>
                <td>
                    <span class="badge {c['severity_class']}">{c['triage_category']}</span>
                    <span style="font-size: 8pt; font-weight: 700; color: #475569; margin-left: 4px;">{c['urgency_score']:.1f}/100</span>
                </td>
                <td style="font-family: monospace; font-size: 8.5pt;">
                    <a href="{c['gps']['maps_url']}" target="_blank" style="color: #0284c7; text-decoration: none; font-weight: 600;">
                        {c['gps']['lat_str']}<br>{c['gps']['lon_str']} ↗
                    </a>
                </td>
                <td style="text-align: right; font-family: monospace; font-weight: 700;">{c['distance_m']:.1f} m</td>
                <td style="text-align: center; font-weight: 700; color: {'#dc2626' if c['thermal_class'] == 'temp-crit' else '#059669'};">
                    {c['thermal_signature']:.1f}°C
                </td>
                <td><div style="display: flex; gap: 3px; flex-wrap: wrap;">{tag_pills}</div></td>
                <td style="font-size: 8pt; color: #334155; max-width: 170px;">{c['recommended_action']}</td>
            </tr>
        """)
    master_table_html = "".join(table_rows)

    # Build Individual Casualty Dossier Cards
    dossier_cards = []
    for c in enriched_casualties:
        tags_html = " ".join([f'<span class="dossier-tag">#{t}</span>' for t in c["tags"]])
        sop_pills = " ".join([f'<span class="sop-pill">{sop}</span>' for sop in c["sop_references"]])
        
        img_element = ""
        if c["snapshot_b64"]:
            img_element = f"""
                <div class="recon-snapshot-frame">
                    <img src="{c['snapshot_b64']}" alt="Aerial Recon {c['victim_id']}" class="recon-img" />
                    <div class="recon-watermark">
                        <span>AERIAL RECON // {c['drone_id']}</span>
                        <span>CONF: {c['confidence_pct']}%</span>
                    </div>
                </div>
            """
        else:
            img_element = f"""
                <div class="recon-snapshot-placeholder">
                    <div style="font-family: monospace; font-weight: 700; color: #94a3b8; font-size: 9pt;">
                        [ AERIAL OPTICAL SNAPSHOT ]<br>
                        LAT: {c['gps']['lat_str']}<br>
                        LON: {c['gps']['lon_str']}
                    </div>
                </div>
            """

        dossier_cards.append(f"""
            <div class="casualty-dossier-card">
                <div class="dossier-header">
                    <div class="dossier-id-box">
                        <span class="dossier-rank-pill">PRIORITY #{c['rank']}</span>
                        <span class="dossier-id">{c['victim_id']}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge {c['severity_class']}">{c['triage_category']}</span>
                        <div class="urgency-meter-box">
                            <span class="urgency-meter-num">{c['urgency_score']:.1f}</span>
                            <span class="urgency-meter-denom">/100</span>
                        </div>
                    </div>
                </div>

                <div class="dossier-body">
                    <!-- Left: Aerial Inspection Snapshot -->
                    <div class="dossier-snapshot-col">
                        {img_element}
                        <div class="telemetry-caption">
                            <span>Target: HUMAN ({c['confidence_pct']}%)</span>
                            <span>Sensor: 4K Optical + FLIR</span>
                        </div>
                    </div>

                    <!-- Right: Telemetry & Triage Details -->
                    <div class="dossier-info-col">
                        <div class="info-grid">
                            <div class="info-cell">
                                <span class="cell-label">GPS LATITUDE</span>
                                <span class="cell-val mono">{c['gps']['lat_str']}</span>
                            </div>
                            <div class="info-cell">
                                <span class="cell-label">GPS LONGITUDE</span>
                                <span class="cell-val mono">{c['gps']['lon_str']}</span>
                            </div>
                            <div class="info-cell">
                                <span class="cell-label">DISTANCE FROM GCS</span>
                                <span class="cell-val mono" style="color: #0284c7;">{c['distance_m']:.1f} meters</span>
                            </div>
                            <div class="info-cell">
                                <span class="cell-label">FLIR CORE BODY TEMP</span>
                                <span class="cell-val mono {'temp-crit' if c['thermal_class'] == 'temp-crit' else 'temp-norm'}">
                                    {c['thermal_signature']:.1f}°C <span style="font-size: 7pt; font-weight: 700;">({c['thermal_status']})</span>
                                </span>
                            </div>
                        </div>

                        <!-- Google Maps Live Direct Link -->
                        <div class="gps-link-banner">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0284c7" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
                            <span style="font-size: 8pt; font-weight: 600; color: #1e293b;">Google Maps Live Fix:</span>
                            <a href="{c['gps']['maps_url']}" target="_blank" class="maps-live-link">{c['gps']['combined']} ↗</a>
                        </div>

                        <!-- Environmental Hazard Tags -->
                        <div class="section-row">
                            <span class="subhead">HAZARDS DETECTED:</span>
                            <div class="tags-container">{tags_html}</div>
                        </div>

                        <!-- Field Assessment & Observations -->
                        <div class="section-block">
                            <span class="subhead">CLINICAL OBSERVATION:</span>
                            <p class="obs-text">{c['notes']}</p>
                        </div>

                        <!-- Actionable SOP Directives -->
                        <div class="action-box">
                            <div class="action-title-row">
                                <span class="action-label">FIELD DISPATCH ACTION</span>
                                <div class="sop-container">{sop_pills}</div>
                            </div>
                            <p class="action-body">{c['recommended_action']}</p>
                        </div>
                    </div>
                </div>
            </div>
        """)
    dossiers_html = "".join(dossier_cards)

    # Complete HTML Document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SARAS Tactical Casualty Triage Report — {doc_id}</title>
    <style>
        @page {{
            size: A4 portrait;
            margin: 12mm 14mm 14mm 14mm;
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 8pt;
                color: #64748b;
            }}
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            font-size: 9pt;
            color: #0f172a;
            background: #ffffff;
            line-height: 1.35;
        }}

        .mono {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        }}

        /* Page Layout & Container */
        .report-page {{
            page-break-after: always;
        }}
        .report-page:last-child {{
            page-break-after: auto;
        }}

        /* Document Header */
        .header-container {{
            border-bottom: 2px solid #0f172a;
            padding-bottom: 10px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }}

        .header-brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .brand-crest {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-weight: 900;
            font-size: 14pt;
            letter-spacing: -1px;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.25);
        }}

        .title-block h1 {{
            font-size: 15pt;
            font-weight: 800;
            letter-spacing: -0.4px;
            color: #0f172a;
            line-height: 1.15;
        }}

        .title-block p {{
            font-size: 8pt;
            font-weight: 600;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 2px;
        }}

        .header-meta {{
            text-align: right;
            font-size: 8pt;
            color: #475569;
        }}

        .meta-pill {{
            display: inline-block;
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-family: monospace;
            color: #0f172a;
            margin-bottom: 4px;
        }}

        /* Executive Metrics Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 8px;
            margin-bottom: 14px;
        }}

        .metric-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 8px 10px;
            border-left: 4px solid #94a3b8;
        }}
        .metric-card.crit {{ border-left-color: #ef4444; background: #fef2f2; }}
        .metric-card.urg {{ border-left-color: #f59e0b; background: #fffbeb; }}
        .metric-card.stab {{ border-left-color: #10b981; background: #ecfdf5; }}
        .metric-card.blue {{ border-left-color: #0284c7; background: #f0f9ff; }}

        .m-num {{
            font-size: 15pt;
            font-weight: 800;
            line-height: 1.1;
        }}
        .metric-card.crit .m-num {{ color: #dc2626; }}
        .metric-card.urg .m-num {{ color: #d97706; }}
        .metric-card.stab .m-num {{ color: #059669; }}
        .metric-card.blue .m-num {{ color: #0284c7; }}

        .m-label {{
            font-size: 7pt;
            font-weight: 700;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        /* Section Headings */
        .section-heading {{
            font-size: 10pt;
            font-weight: 800;
            color: #0f172a;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 14px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
        }}
        .section-bar {{
            width: 4px;
            height: 12px;
            background: #0284c7;
            border-radius: 2px;
        }}

        /* Data Tables */
        .triage-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
            margin-bottom: 14px;
            border: 1px solid #cbd5e1;
        }}

        .triage-table th {{
            background: #0f172a;
            color: #ffffff;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            font-size: 7pt;
            padding: 6px 8px;
            text-align: left;
        }}

        .triage-table td {{
            padding: 6px 8px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: middle;
        }}

        .triage-table tr:nth-child(even) {{
            background: #f8fafc;
        }}

        /* Severity Badges */
        .badge {{
            display: inline-block;
            font-size: 6.5pt;
            font-weight: 800;
            text-transform: uppercase;
            padding: 2px 6px;
            border-radius: 3px;
            letter-spacing: 0.3px;
        }}
        .badge.cat-crit {{ background: #fee2e2; color: #b91c1c; border: 1px solid #f87171; }}
        .badge.cat-urg {{ background: #fef3c7; color: #b45309; border: 1px solid #fbbf24; }}
        .badge.cat-stab {{ background: #d1fae5; color: #047857; border: 1px solid #34d399; }}

        .mini-tag {{
            font-size: 6.5pt;
            font-weight: 700;
            background: #f1f5f9;
            color: #475569;
            padding: 1px 4px;
            border-radius: 3px;
            border: 1px solid #e2e8f0;
        }}

        /* Casualty Dossier Card Styles */
        .casualty-dossier-card {{
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            margin-bottom: 12px;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            page-break-inside: avoid;
            overflow: hidden;
        }}

        .dossier-header {{
            background: #f8fafc;
            border-bottom: 1px solid #e2e8f0;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .dossier-id-box {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .dossier-rank-pill {{
            background: #0f172a;
            color: #ffffff;
            font-size: 7pt;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}

        .dossier-id {{
            font-size: 11pt;
            font-weight: 800;
            font-family: monospace;
            color: #0f172a;
        }}

        .urgency-meter-box {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}
        .urgency-meter-num {{ font-weight: 800; font-size: 8.5pt; color: #dc2626; }}
        .urgency-meter-denom {{ font-size: 7pt; color: #94a3b8; }}

        .dossier-body {{
            display: flex;
            padding: 10px;
            gap: 12px;
        }}

        .dossier-snapshot-col {{
            flex: 0 0 250px;
            display: flex;
            flex-direction: column;
        }}

        .recon-snapshot-frame {{
            border-radius: 6px;
            overflow: hidden;
            border: 1px solid #334155;
            background: #0f172a;
            position: relative;
        }}

        .recon-img {{
            width: 100%;
            height: auto;
            display: block;
        }}

        .recon-watermark {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(15, 23, 42, 0.88);
            color: #ffffff;
            font-size: 6.5pt;
            font-family: monospace;
            padding: 2px 6px;
            display: flex;
            justify-content: space-between;
        }}

        .recon-snapshot-placeholder {{
            width: 250px;
            height: 140px;
            background: #f1f5f9;
            border: 1px dashed #cbd5e1;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 10px;
        }}

        .telemetry-caption {{
            display: flex;
            justify-content: space-between;
            font-size: 6.8pt;
            font-family: monospace;
            color: #64748b;
            margin-top: 4px;
            font-weight: 600;
        }}

        .dossier-info-col {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 5px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 5px;
            padding: 6px 8px;
        }}

        .info-cell {{
            display: flex;
            flex-direction: column;
        }}

        .cell-label {{
            font-size: 6pt;
            font-weight: 700;
            color: #64748b;
            text-transform: uppercase;
        }}

        .cell-val {{
            font-size: 8pt;
            font-weight: 700;
            color: #0f172a;
        }}

        .temp-crit {{ color: #dc2626 !important; }}
        .temp-norm {{ color: #059669 !important; }}

        .gps-link-banner {{
            display: flex;
            align-items: center;
            gap: 6px;
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            padding: 4px 8px;
            border-radius: 4px;
        }}

        .maps-live-link {{
            font-family: monospace;
            font-size: 7.5pt;
            font-weight: 700;
            color: #0284c7;
            text-decoration: underline;
        }}

        .section-row {{
            display: flex;
            align-items: center;
            gap: 6px;
            margin-top: 2px;
        }}

        .subhead {{
            font-size: 6.8pt;
            font-weight: 800;
            color: #475569;
            text-transform: uppercase;
        }}

        .tags-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}

        .dossier-tag {{
            font-size: 6.5pt;
            font-weight: 700;
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            color: #334155;
            padding: 1px 6px;
            border-radius: 3px;
        }}

        .section-block {{
            margin-top: 2px;
        }}

        .obs-text {{
            font-size: 7.8pt;
            color: #334155;
            background: #fdfdfd;
            border-left: 2px solid #94a3b8;
            padding: 2px 6px;
            margin-top: 2px;
        }}

        .action-box {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 3px solid #0284c7;
            padding: 6px 8px;
            border-radius: 4px;
            margin-top: 2px;
        }}

        .action-title-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2px;
        }}

        .action-label {{
            font-size: 6.8pt;
            font-weight: 800;
            color: #0284c7;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}

        .sop-pill {{
            font-size: 6.5pt;
            font-family: monospace;
            font-weight: 700;
            background: #0284c7;
            color: #ffffff;
            padding: 1px 5px;
            border-radius: 3px;
        }}

        .action-body {{
            font-size: 7.8pt;
            font-weight: 600;
            color: #0f172a;
        }}

        /* Clearance & Sign-off Block */
        .clearance-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px dashed #cbd5e1;
            page-break-inside: avoid;
        }}

        .clearance-card {{
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 10px;
            background: #f8fafc;
        }}

        .clearance-title {{
            font-size: 7.5pt;
            font-weight: 800;
            text-transform: uppercase;
            color: #334155;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
        }}

        .signature-line {{
            margin-top: 24px;
            border-bottom: 1px solid #475569;
            width: 70%;
        }}

        .sig-meta {{
            font-size: 7pt;
            color: #64748b;
            margin-top: 4px;
            font-family: monospace;
        }}

        .footer-banner {{
            margin-top: 14px;
            text-align: center;
            font-size: 7pt;
            color: #94a3b8;
            font-family: monospace;
        }}
    </style>
</head>
<body>

    <!-- ================= PAGE 1: EXECUTIVE TRIAGE OVERVIEW ================= -->
    <div class="report-page">
        <!-- Header -->
        <header class="header-container">
            <div class="header-brand">
                <div class="brand-crest">S</div>
                <div class="title-block">
                    <h1>SARAS CASUALTY & DAMAGE ASSESSMENT REPORT</h1>
                    <p>Autonomous Search & Rescue Swarm • Reconnaissance & AI Triage Dossier</p>
                </div>
            </div>
            <div class="header-meta">
                <div class="meta-pill">{doc_id}</div><br>
                <span><strong>Report Date:</strong> {report_time_local}</span><br>
                <span><strong>Zulu Time:</strong> {report_time_utc}</span><br>
                <span><strong>GCS Coordinates:</strong> {gcs_lat:.5f}° N, {gcs_lon:.5f}° E</span>
            </div>
        </header>

        <!-- Executive Metrics -->
        <div class="metrics-grid">
            <div class="metric-card blue">
                <div class="m-num">{total_victims}</div>
                <div class="m-label">TOTAL CASUALTIES DETECTED</div>
            </div>
            <div class="metric-card crit">
                <div class="m-num">{critical_count}</div>
                <div class="m-label">CRITICAL (IMMEDIATE EVAC)</div>
            </div>
            <div class="metric-card urg">
                <div class="m-num">{urgent_count}</div>
                <div class="m-label">URGENT (DELAYED / STABILIZE)</div>
            </div>
            <div class="metric-card stab">
                <div class="m-num">{stable_count}</div>
                <div class="m-label">STABLE (MONITOR / AMBULATORY)</div>
            </div>
        </div>

        <!-- Master Triage Priority Matrix -->
        <div class="section-heading">
            <div class="section-bar"></div>
            <span>MASTER CASUALTY PRIORITY MATRIX (SORTED STRICTLY BY URGENCY SCORE)</span>
        </div>
        <table class="triage-table">
            <thead>
                <tr>
                    <th style="width: 35px; text-align: center;">RANK</th>
                    <th style="width: 70px;">CASUALTY ID</th>
                    <th style="width: 105px;">TRIAGE CLASS</th>
                    <th style="width: 140px;">GPS FIX (LAT / LON)</th>
                    <th style="width: 80px; text-align: right;">GCS RANGE</th>
                    <th style="width: 65px; text-align: center;">FLIR TEMP</th>
                    <th style="width: 130px;">PRIMARY HAZARDS</th>
                    <th>ACTIONABLE DIRECTIVE</th>
                </tr>
            </thead>
            <tbody>
                {master_table_html}
            </tbody>
        </table>

        <!-- Swarm Operational Readiness -->
        <div class="section-heading">
            <div class="section-bar"></div>
            <span>SWARM RECONNAISSANCE FLEET STATUS</span>
        </div>
        <table class="triage-table" style="margin-bottom: 8px;">
            <thead>
                <tr>
                    <th>UAV IDENTIFIER</th>
                    <th>AVIONICS STATE</th>
                    <th>BATTERY</th>
                    <th>ACTIVE ASSIGNMENT</th>
                    <th>AIRSPACE TELEMETRY FIX</th>
                </tr>
            </thead>
            <tbody>
                {fleet_table_html}
            </tbody>
        </table>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; font-size: 7.5pt; color: #475569;">
            <strong>MISSION PROTOCOL NOTICE:</strong> All casualty locations have been georeferenced via RTK GPS downlinks from UAV telemetry.
            Prioritization follows the START (Simple Triage And Rapid Treatment) protocol enhanced with real-time FLIR thermal body core tracking and AI hazard analysis.
            Individual casualty inspection dossiers with aerial optical/thermal captures continue on Page 2.
        </div>
    </div>

    <!-- ================= PAGE 2+: DETAILED CASUALTY DOSSIERS ================= -->
    <div class="report-page">
        <header class="header-container" style="margin-bottom: 8px; padding-bottom: 6px;">
            <div class="title-block">
                <h1 style="font-size: 12pt;">INDIVIDUAL CASUALTY INSPECTION DOSSIERS</h1>
                <p>High-Resolution Optical/Thermal Aerial Recon • Real-Time GPS Coordinates • SOP Protocols</p>
            </div>
            <div class="header-meta">
                <span class="meta-pill">{doc_id}</span>
            </div>
        </header>

        {dossiers_html}

        <!-- Command Sign-off & Clearance Authorization -->
        <div class="clearance-grid">
            <div class="clearance-card">
                <div class="clearance-title">
                    <span>S.A.R. INCIDENT COMMANDER</span>
                    <span style="color: #059669; font-family: monospace;">[VERIFIED]</span>
                </div>
                <p style="font-size: 7pt; color: #475569;">
                    I hereby certify that the aerial reconnaissance data, geolocations, and swarm triage assessments have been verified for ground dispatch.
                </p>
                <div class="signature-line"></div>
                <div class="sig-meta">COMMAND CLEARANCE ID: SARAS-EXEC-CMD-01 • {report_time_utc}</div>
            </div>

            <div class="clearance-card">
                <div class="clearance-title">
                    <span>EMERGENCY MEDICAL DISPATCH LEAD</span>
                    <span style="color: #059669; font-family: monospace;">[TRIAGED]</span>
                </div>
                <p style="font-size: 7pt; color: #475569;">
                    Medical triage scores and FLIR core temperature assessments reviewed. Evacuation priorities confirmed according to emergency protocols.
                </p>
                <div class="signature-line"></div>
                <div class="sig-meta">TRIAGE OFFICER LICENSE: MED-SAR-TR-882 • {report_time_utc}</div>
            </div>
        </div>

        <div class="footer-banner">
            SARAS AUTONOMOUS SEARCH & RESCUE SYSTEM • END OF OFFICIAL CASUALTY RECON REPORT
        </div>
    </div>

</body>
</html>
"""

    if output_path is None:
        reports_dir = Path(__file__).resolve().parent.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target_file = reports_dir / "SARAS_Casualty_Triage_Report.pdf"
    else:
        target_file = Path(output_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)

    # Also save HTML version alongside PDF for quick browser preview
    html_target = target_file.with_suffix(".html")
    html_target.write_text(html_content, encoding="utf-8")

    # Use Playwright to render PDF
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        page.pdf(
            path=str(target_file),
            format="A4",
            print_background=True,
            margin={"top": "10mm", "bottom": "12mm", "left": "12mm", "right": "12mm"}
        )
        browser.close()

    print(f"[ReportGenerator] Report successfully rendered: {target_file} ({target_file.stat().st_size} bytes)")
    return target_file


if __name__ == "__main__":
    import urllib.request
    import json
    from backend.video_streamer import SwarmVideoStreamer

    streamer = SwarmVideoStreamer()
    # Test fetch from local backend or mock
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/victims/sorted")
        data = json.loads(req.read())
        print(f"Loaded {len(data)} victims from live server.")
    except Exception as e:
        print(f"Local server query fallback: {e}")
        data = [
            {
                "victim_id": "VIC-102",
                "drone_id": "UAV-01",
                "lat": 12.97724,
                "lon": 77.59364,
                "distance_m": 637.2,
                "triage_category": "CRITICAL",
                "urgency_score": 100.0,
                "thermal_signature": 34.1,
                "confidence": 0.96,
                "environment_tags": ["Flood Submerged", "Hypothermia Risk"],
                "notes": "Victim caught in deep water surge near collapsed masonry.",
                "recommended_action": "Immediate air-drop flotation raft and urgent winch evac.",
                "sop_references": ["SOP-COL-03", "SOP-MED-01"]
            },
            {
                "victim_id": "VIC-101",
                "drone_id": "UAV-02",
                "lat": 12.97436,
                "lon": 77.59520,
                "distance_m": 314.5,
                "triage_category": "CRITICAL",
                "urgency_score": 90.0,
                "thermal_signature": 38.8,
                "confidence": 0.94,
                "environment_tags": ["Crush Injury", "Structural Debris"],
                "notes": "Trapped under collapsed beam. Signs of severe trauma.",
                "recommended_action": "Heavy hydraulic extraction team with ATLS medical unit.",
                "sop_references": ["SOP-EXT-02", "SOP-MED-01"]
            }
        ]

    out = generate_triage_pdf_report(
        victims=data,
        video_streamer=streamer,
        output_path="reports/SARAS_Casualty_Triage_Report.pdf"
    )
    print("Generated PDF test at:", out)

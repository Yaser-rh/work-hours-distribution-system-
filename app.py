"""
Flask REST API backend for the Driver Shift & Timesheet Distribution System.
Wraps existing db/models.py, solver/sat_solver.py, and exporter/docx_exporter.py
with a JSON API and serves the web frontend from web/.
"""

import os
import sys
import json
import calendar
import sqlite3
import webbrowser
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import initialize_database
import db.models as models
import solver.sat_solver as sat_solver
import exporter.docx_exporter as docx_exporter

# System logs list to keep logs in memory
system_logs = []

def add_log(level, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'level': level,  # 'INFO', 'WARNING', 'ERROR'
        'message': message
    }
    system_logs.append(log_entry)
    if len(system_logs) > 500:
        system_logs.pop(0)

# Add startup log
add_log('INFO', "Driver Shift & Timesheet System Backend initialized.")

app = Flask(__name__, static_folder='web', static_url_path='')


# ==============================================================================
# Static file serving
# ==============================================================================

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')


# ==============================================================================
# Cities API
# ==============================================================================

@app.route('/api/cities', methods=['GET'])
def api_get_cities():
    cities = models.get_cities()
    # Enrich with driver count
    for city in cities:
        ts = models.get_timesheets(city_id=city['id'])
        city['driver_count'] = len(set(t['employee_id'] for t in ts))
    return jsonify(cities)

@app.route('/api/cities', methods=['POST'])
def api_add_city():
    data = request.json
    try:
        city_id = models.add_city(data['name'], data['start_time'], data['end_time'])
        add_log('INFO', f"City added: '{data['name']}' (ID: {city_id}, hours: {data['start_time']}-{data['end_time']})")
        return jsonify({'id': city_id, 'success': True}), 201
    except sqlite3.IntegrityError:
        add_log('WARNING', f"Failed to add city '{data['name']}': name already exists.")
        return jsonify({'error': 'A city with this name already exists.'}), 409

@app.route('/api/cities/<int:city_id>', methods=['PUT'])
def api_update_city(city_id):
    data = request.json
    try:
        models.update_city(city_id, data['name'], data['start_time'], data['end_time'])
        add_log('INFO', f"City updated: '{data['name']}' (ID: {city_id}, hours: {data['start_time']}-{data['end_time']})")
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        add_log('WARNING', f"Failed to update city ID {city_id}: name already exists.")
        return jsonify({'error': 'A city with this name already exists.'}), 409

@app.route('/api/cities/<int:city_id>', methods=['DELETE'])
def api_delete_city(city_id):
    try:
        models.delete_city(city_id)
        add_log('INFO', f"City deleted: ID {city_id}")
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        add_log('WARNING', f"Failed to delete city ID {city_id}: timesheets reference it.")
        return jsonify({'error': 'Cannot delete city: timesheets reference it.'}), 409


# ==============================================================================
# Drivers API
# ==============================================================================

@app.route('/api/drivers', methods=['GET'])
def api_get_drivers():
    return jsonify(models.get_employees())

@app.route('/api/drivers', methods=['POST'])
def api_add_driver():
    data = request.json
    try:
        emp_id = models.add_employee(data['name'], data['personal_id'])
        add_log('INFO', f"Driver added: '{data['name']}' (ID: {emp_id}, Personal ID: {data['personal_id']})")
        return jsonify({'id': emp_id, 'success': True}), 201
    except sqlite3.IntegrityError:
        add_log('WARNING', f"Failed to add driver '{data['name']}': Personal ID already exists.")
        return jsonify({'error': 'A driver with this Personal ID already exists.'}), 409

@app.route('/api/drivers/<int:driver_id>', methods=['PUT'])
def api_update_driver(driver_id):
    data = request.json
    try:
        models.update_employee(driver_id, data['name'], data['personal_id'])
        add_log('INFO', f"Driver updated: '{data['name']}' (ID: {driver_id}, Personal ID: {data['personal_id']})")
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        add_log('WARNING', f"Failed to update driver ID {driver_id}: Personal ID already exists.")
        return jsonify({'error': 'A driver with this Personal ID already exists.'}), 409

@app.route('/api/drivers/<int:driver_id>', methods=['DELETE'])
def api_delete_driver(driver_id):
    try:
        models.delete_employee(driver_id)
        add_log('INFO', f"Driver deleted: ID {driver_id}")
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        add_log('WARNING', f"Failed to delete driver ID {driver_id}: timesheets reference them.")
        return jsonify({'error': 'Cannot delete driver: timesheets reference them.'}), 409

@app.route('/api/drivers/<int:driver_id>/timesheets', methods=['GET'])
def api_get_driver_timesheets(driver_id):
    ts = models.get_timesheets(employee_id=driver_id)
    return jsonify(ts)


# ==============================================================================
# Timesheets API
# ==============================================================================

@app.route('/api/timesheets', methods=['GET'])
def api_get_timesheets():
    city_id = request.args.get('city_id', type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    status = request.args.get('status')
    ts = models.get_timesheets(city_id=city_id, year=year, month=month, status=status)
    # Enrich with actual hours
    for t in ts:
        detail = models.get_timesheet_with_entries(t['id'])
        t['actual_hours'] = sum(e['hours_worked'] for e in detail.get('entries', []))
    return jsonify(ts)

@app.route('/api/timesheets', methods=['POST'])
def api_create_timesheets():
    """Create one or more timesheets. Accepts a list of {employee_id, city_id, year, month, target_hours}."""
    data = request.json
    items = data if isinstance(data, list) else [data]
    created = []
    errors = []
    for item in items:
        try:
            ts_id = models.create_timesheet(
                item['employee_id'], item['city_id'],
                item['year'], item['month'], item['target_hours']
            )
            created.append({'id': ts_id, 'employee_id': item['employee_id']})
        except sqlite3.IntegrityError:
            errors.append({
                'employee_id': item['employee_id'],
                'error': 'Timesheet already exists for this driver/city/month.'
            })
    return jsonify({'created': created, 'errors': errors}), 201 if created else 409

@app.route('/api/timesheets/<int:ts_id>', methods=['GET'])
def api_get_timesheet(ts_id):
    detail = models.get_timesheet_with_entries(ts_id)
    if not detail:
        return jsonify({'error': 'Timesheet not found.'}), 404
    return jsonify(detail)

@app.route('/api/timesheets/<int:ts_id>', methods=['DELETE'])
def api_delete_timesheet(ts_id):
    try:
        models.delete_timesheet(ts_id)
        add_log('INFO', f"Deleted timesheet ID {ts_id}")
        return jsonify({'success': True})
    except Exception as e:
        add_log('ERROR', f"Failed to delete timesheet: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timesheets/<int:ts_id>/status', methods=['PUT'])
def api_update_status(ts_id):
    data = request.json
    try:
        models.update_timesheet_status(ts_id, data['status'])
        if data['status'] == 'Finalized':
            models.set_distribution_lock(ts_id, True)
            add_log('INFO', f"Timesheet finalized: ID {ts_id}")
        elif data['status'] == 'Draft':
            models.set_distribution_lock(ts_id, False)
            add_log('INFO', f"Timesheet reverted to Draft (unlocked): ID {ts_id}")
        return jsonify({'success': True})
    except ValueError as e:
        add_log('ERROR', f"Failed to update timesheet status: {str(e)}")
        return jsonify({'error': str(e)}), 400

@app.route('/api/timesheets/<int:ts_id>/unlock', methods=['POST'])
def api_unlock_timesheet(ts_id):
    try:
        models.set_distribution_lock(ts_id, False)
        add_log('INFO', f"Timesheet unlocked: ID {ts_id}")
        return jsonify({'success': True})
    except Exception as e:
        add_log('ERROR', f"Failed to unlock timesheet ID {ts_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/timesheets/<int:ts_id>/entries', methods=['PUT'])
def api_save_entries(ts_id):
    data = request.json
    entries = data.get('entries', [])
    lock = data.get('lock', False)
    try:
        models.save_daily_entries(ts_id, entries)
        msg = f"Saved {len(entries)} manual entries for timesheet ID {ts_id}"
        if lock:
            models.set_distribution_lock(ts_id, True)
            msg += " (and locked it)"
        add_log('INFO', msg)
        return jsonify({'success': True})
    except Exception as e:
        add_log('ERROR', f"Failed to save manual entries: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Solver API
# ==============================================================================

@app.route('/api/timesheets/solve', methods=['POST'])
def api_solve():
    """
    Solve for the given timesheet IDs.
    Expects: { timesheet_ids: [int], redistribute_around: int|null }
    redistribute_around: if set, this timesheet is treated as locked/fixed and
    the other IDs are solved around it. Returns count of altered schedules.
    """
    data = request.json
    timesheet_ids = data.get('timesheet_ids', [])
    redistribute_around_id = data.get('redistribute_around')
    timeout = data.get('timeout', 30.0)
    try:
        timeout = float(timeout)
        if timeout <= 0:
            timeout = 30.0
    except (ValueError, TypeError):
        timeout = 30.0

    if not timesheet_ids:
        return jsonify({'error': 'No timesheet IDs provided.'}), 400

    # Load first timesheet to get city/month context
    first_ts = models.get_timesheet_with_entries(timesheet_ids[0])
    if not first_ts:
        return jsonify({'error': 'Timesheet not found.'}), 404

    city_id = first_ts['city_id']
    year = first_ts['year']
    month = first_ts['month']
    _, num_days = calendar.monthrange(year, month)

    # Get city details
    cities = models.get_cities()
    city = next((c for c in cities if c['id'] == city_id), None)
    if not city:
        return jsonify({'error': 'City not found.'}), 404

    city_start = sat_solver.clock_to_units(city['start_time'])
    city_end = sat_solver.clock_to_units(city['end_time'])

    # Collect all timesheets for this city/month
    all_ts = models.get_timesheets(city_id=city_id, year=year, month=month)

    # Determine which timesheets to solve vs treat as locked background
    solve_ids = set(timesheet_ids)
    drivers = []
    locked_entries = {}

    # Capture pre-solve state for "before vs after" comparison
    pre_solve_state = {}
    for ts_id in timesheet_ids:
        detail = models.get_timesheet_with_entries(ts_id)
        if detail:
            pre_solve_state[ts_id] = sum(1 for e in detail.get('entries', []) if e['hours_worked'] > 0)

    for ts in all_ts:
        ts_detail = models.get_timesheet_with_entries(ts['id'])
        if not ts_detail:
            continue

        if ts['id'] in solve_ids and ts['id'] != redistribute_around_id:
            # This is a timesheet to solve
            if ts['status'] == 'Finalized' or ts['is_distribution_locked']:
                # Finalized/locked timesheets become background constraints
                locked_entries[ts['employee_id']] = ts_detail.get('entries', [])
            else:
                drivers.append(sat_solver.DriverSpec(
                    employee_id=ts['employee_id'],
                    target_units=sat_solver.hours_to_units(ts['target_hours']),
                    name=ts['employee_name']
                ))
        else:
            # Background locked timesheet (not being solved)
            entries = ts_detail.get('entries', [])
            if entries:
                if ts['employee_id'] in locked_entries:
                    locked_entries[ts['employee_id']].extend(entries)
                else:
                    locked_entries[ts['employee_id']] = entries

    # Build boundary and cross-city data
    prev_month_boundary = {}
    cross_city_active = {}
    for d_spec in drivers:
        prev_month_boundary[d_spec.employee_id] = models.get_previous_month_boundary(
            d_spec.employee_id, year, month
        )
        cross_city_active[d_spec.employee_id] = models.get_cross_city_active_days(
            d_spec.employee_id, year, month, city_id
        )

    # Get existing coverage (from timesheets NOT in our solve set and NOT locked)
    exclude_ids = list(solve_ids)
    existing_coverage = models.get_city_coverage(city_id, year, month, exclude_timesheet_ids=exclude_ids)

    mode = 'batch' if len(drivers) > 1 else 'incremental'

    solver_input = sat_solver.SolverInput(
        drivers=drivers,
        city_start=city_start,
        city_end=city_end,
        num_days=num_days,
        prev_month_boundary=prev_month_boundary,
        cross_city_active=cross_city_active,
        existing_coverage=existing_coverage,
        locked_entries=locked_entries,
        mode=mode
    )

    add_log('INFO', f"Running solver in '{mode}' mode for {len(drivers)} active driver(s) (City ID: {city_id}, Month: {month}/{year}, timeout: {timeout}s)")
    
    result = sat_solver.solve(solver_input, timeout=timeout)

    if result.status == 'failed':
        add_log('WARNING', f"Solver failed to find a feasible schedule (solved in {result.solve_time_seconds:.2f}s)")
        return jsonify({
            'status': 'failed',
            'message': 'Solver could not find a feasible schedule.',
            'solve_time': round(result.solve_time_seconds, 2)
        }), 200

    # Save results to database
    altered_count = 0
    for ts in all_ts:
        if ts['employee_id'] in result.schedules:
            schedule = result.schedules[ts['employee_id']]
            # Only save if this is one of the IDs we were asked to solve
            if ts['id'] in solve_ids and ts['id'] != redistribute_around_id:
                entries = []
                for day_entry in schedule:
                    work_date = f"{year}-{month:02d}-{day_entry.day:02d}"
                    break_str = f"00:{day_entry.break_minutes:02d}" if day_entry.break_minutes > 0 else ""
                    entries.append({
                        'work_date': work_date,
                        'hours_worked': day_entry.hours,
                        'start_time': day_entry.start_time,
                        'end_time': day_entry.end_time,
                        'break_duration': break_str,
                        'remarks': ''
                    })
                models.save_daily_entries(ts['id'], entries)

                # Count altered schedules for the "before vs after" feedback
                post_count = sum(1 for e in entries if e['hours_worked'] > 0)
                pre_count = pre_solve_state.get(ts['id'], 0)
                if post_count != pre_count or pre_count > 0:
                    altered_count += 1

    add_log('INFO', f"Solver successful. Altered {altered_count} driver schedule(s) in {result.solve_time_seconds:.2f}s")

    return jsonify({
        'status': result.status,
        'target_deviation': result.target_deviation,
        'solve_time': round(result.solve_time_seconds, 2),
        'altered_count': altered_count,
        'message': f"Solver completed ({result.status}). {altered_count} schedule(s) updated."
    })


# ==============================================================================
# Export API
# ==============================================================================

@app.route('/api/timesheets/<int:ts_id>/export', methods=['POST'])
def api_export_timesheet(ts_id):
    detail = models.get_timesheet_with_entries(ts_id)
    if not detail:
        return jsonify({'error': 'Timesheet not found.'}), 404

    # Generate file in a temp location
    clean_name = "".join(c for c in detail['employee_name'] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    filename = f"timesheet_{clean_name}_{detail['month']:02d}_{detail['year']}.docx"
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exports', filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    docx_exporter.generate_docx(
        employee_name=detail['employee_name'],
        personal_id=detail['personal_id'],
        city_name=detail['city_name'],
        year=detail['year'],
        month=detail['month'],
        daily_entries=detail['entries'],
        target_hours=detail['target_hours'],
        output_path=output_path
    )

    return send_file(output_path, as_attachment=True, download_name=filename)


# ==============================================================================
# Analytics API
# ==============================================================================

@app.route('/api/analytics/driver/<int:driver_id>', methods=['GET'])
def api_driver_analytics(driver_id):
    timesheets = models.get_timesheets(employee_id=driver_id)
    timesheets = sorted(timesheets, key=lambda t: (t['year'], t['month']))
    result = []
    for ts in timesheets:
        detail = models.get_timesheet_with_entries(ts['id'])
        actual = sum(e['hours_worked'] for e in detail.get('entries', []))
        result.append({
            'label': f"{ts['month']:02d}/{ts['year']}",
            'city': ts['city_name'],
            'target_hours': ts['target_hours'],
            'actual_hours': actual,
            'status': ts['status']
        })
    return jsonify(result)

@app.route('/api/analytics/coverage', methods=['GET'])
def api_city_coverage():
    city_id = request.args.get('city_id', type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not all([city_id, year, month]):
        return jsonify({'error': 'city_id, year, month required.'}), 400

    cities = models.get_cities()
    city = next((c for c in cities if c['id'] == city_id), None)
    if not city:
        return jsonify({'error': 'City not found.'}), 404

    _, num_days = calendar.monthrange(year, month)
    coverage = models.get_city_coverage(city_id, year, month)

    c_start = sat_solver.clock_to_units(city['start_time'])
    c_end = sat_solver.clock_to_units(city['end_time'])

    # Build time labels
    time_labels = []
    for slot in range(c_start, c_end):
        time_labels.append(sat_solver.units_to_clock(slot))

    # Build matrix
    matrix = []
    for d in range(1, num_days + 1):
        day_cov = coverage.get(d, {})
        row = [day_cov.get(slot, 0) for slot in range(c_start, c_end)]
        matrix.append(row)

    return jsonify({
        'num_days': num_days,
        'time_labels': time_labels,
        'matrix': matrix,
        'city_start': city['start_time'],
        'city_end': city['end_time']
    })


# ==============================================================================
# Dashboard API
# ==============================================================================

@app.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    cities = models.get_cities()
    drivers = models.get_employees()
    timesheets = models.get_timesheets()
    finalized = [t for t in timesheets if t['status'] == 'Finalized']
    draft = [t for t in timesheets if t['status'] == 'Draft']

    # Recent timesheets (last 5)
    recent = timesheets[:5]
    for r in recent:
        detail = models.get_timesheet_with_entries(r['id'])
        r['actual_hours'] = sum(e['hours_worked'] for e in detail.get('entries', []))

    return jsonify({
        'city_count': len(cities),
        'driver_count': len(drivers),
        'timesheet_count': len(timesheets),
        'finalized_count': len(finalized),
        'draft_count': len(draft),
        'recent': recent
    })


# ==============================================================================
# Database Tools API
# ==============================================================================

@app.route('/api/database/backup', methods=['POST'])
def api_backup():
    data = request.json
    dest = data.get('path')
    if not dest:
        # Default backup path
        dest = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups',
                           f"timesheets_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        models.backup_database(dest)
        add_log('INFO', f"Database successfully backed up to: {dest}")
        return jsonify({'success': True, 'path': dest})
    except Exception as e:
        add_log('ERROR', f"Database backup failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/restore', methods=['POST'])
def api_restore():
    data = request.json
    src = data.get('path')
    if not src:
        add_log('WARNING', "Database restore failed: No backup path provided.")
        return jsonify({'error': 'No backup path provided.'}), 400
    try:
        models.restore_database(src)
        initialize_database()
        add_log('INFO', f"Database successfully restored from: {src}")
        return jsonify({'success': True})
    except Exception as e:
        add_log('ERROR', f"Database restore failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Logs API
# ==============================================================================

@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    return jsonify(system_logs)

@app.route('/api/logs/clear', methods=['POST'])
def api_clear_logs():
    system_logs.clear()
    add_log('INFO', "System logs cleared.")
    return jsonify({'success': True})


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == '__main__':
    initialize_database()
    port = 5000
    # Auto-open browser after a short delay
    def open_browser():
        webbrowser.open(f'http://localhost:{port}')
    threading.Timer(1.5, open_browser).start()
    print(f"\n  Driver Shift & Timesheet System")
    print(f"  Running at http://localhost:{port}\n")
    app.run(host='127.0.0.1', port=port, debug=False)

-- =============================================================
-- RailMadat — Create Missing Tables
-- Paste this into Supabase SQL Editor and run
-- =============================================================

-- 1. Equipment table
CREATE TABLE IF NOT EXISTS equipment (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    equipment_id TEXT UNIQUE NOT NULL,
    equipment_type TEXT NOT NULL,
    department TEXT NOT NULL,
    home_section_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Available',
    assigned_team_id TEXT,
    last_calibration_date DATE,
    calibration_due_date DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_equipment_department ON equipment(department);
CREATE INDEX IF NOT EXISTS idx_equipment_section ON equipment(home_section_id);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);

ALTER TABLE equipment ENABLE ROW LEVEL SECURITY;
CREATE POLICY equipment_read_all ON equipment FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY equipment_write_manager ON equipment FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role IN ('Maintenance_Manager', 'Administrator'))
);

-- 2. Maintenance history table
CREATE TABLE IF NOT EXISTS maintenance_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    record_id TEXT UNIQUE NOT NULL,
    asset_id TEXT NOT NULL,
    task_id TEXT,
    scheduled_date DATE,
    maintenance_date DATE,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    maintenance_type TEXT,
    fault_category TEXT,
    root_cause TEXT,
    performed_by TEXT,
    inspection_result TEXT,
    defects_found BOOLEAN DEFAULT FALSE,
    corrective_action TEXT,
    materials_used TEXT,
    work_performed TEXT,
    resolution_type TEXT,
    downtime_minutes INTEGER DEFAULT 0,
    completion_status TEXT,
    next_due_date DATE,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_maint_history_asset ON maintenance_history(asset_id);
CREATE INDEX IF NOT EXISTS idx_maint_history_task ON maintenance_history(task_id);
CREATE INDEX IF NOT EXISTS idx_maint_history_date ON maintenance_history(maintenance_date DESC);

ALTER TABLE maintenance_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY maint_history_read_all ON maintenance_history FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY maint_history_insert_manager ON maintenance_history FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role IN ('Maintenance_Manager', 'Administrator', 'Maintenance_Staff'))
);

-- 3. Maintenance schedules table
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    schedule_id TEXT UNIQUE NOT NULL,
    asset_id TEXT NOT NULL,
    section_id TEXT NOT NULL,
    department TEXT NOT NULL,
    maintenance_type TEXT NOT NULL,
    activity TEXT NOT NULL,
    interval_days INTEGER NOT NULL,
    last_maintenance_date DATE,
    next_due_date DATE,
    is_overdue BOOLEAN DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'Upcoming',
    assigned_team_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_maint_schedules_asset ON maintenance_schedules(asset_id);
CREATE INDEX IF NOT EXISTS idx_maint_schedules_section ON maintenance_schedules(section_id);
CREATE INDEX IF NOT EXISTS idx_maint_schedules_status ON maintenance_schedules(status);
CREATE INDEX IF NOT EXISTS idx_maint_schedules_overdue ON maintenance_schedules(is_overdue);

ALTER TABLE maintenance_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY maint_schedules_read_all ON maintenance_schedules FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY maint_schedules_write_manager ON maintenance_schedules FOR ALL USING (
    EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role IN ('Maintenance_Manager', 'Administrator'))
);

-- 4. Work completion reports table
CREATE TABLE IF NOT EXISTS work_completion_reports (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    completion_report_id TEXT UNIQUE NOT NULL,
    task_id TEXT NOT NULL,
    receiver_department TEXT,
    received_by TEXT,
    received_at TIMESTAMPTZ,
    work_status TEXT NOT NULL,
    completion_percentage INTEGER DEFAULT 0,
    inspection_result TEXT,
    failure_reason TEXT,
    remaining_work_minutes INTEGER DEFAULT 0,
    material_status TEXT,
    safety_status TEXT,
    next_action TEXT,
    remarks TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wcr_task ON work_completion_reports(task_id);
CREATE INDEX IF NOT EXISTS idx_wcr_status ON work_completion_reports(work_status);

ALTER TABLE work_completion_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY wcr_read_all ON work_completion_reports FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY wcr_insert_staff ON work_completion_reports FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role IN ('Maintenance_Staff', 'Maintenance_Manager', 'Administrator'))
);

-- 5. Auto-update triggers for new tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_equipment_updated_at ON equipment;
CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_maint_schedules_updated_at ON maintenance_schedules;
CREATE TRIGGER update_maint_schedules_updated_at BEFORE UPDATE ON maintenance_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

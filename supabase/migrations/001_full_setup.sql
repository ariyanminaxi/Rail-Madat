-- =============================================================
-- RailMadat — Complete Supabase Setup
-- Paste this entire file into Supabase SQL Editor and click Run
-- =============================================================

-- =============================================================
-- PART 1: Auto-generate ID triggers
-- =============================================================

-- Auto-generate complaint_id (C-0001, C-0002, ...)
CREATE OR REPLACE FUNCTION generate_complaint_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.complaint_id IS NULL OR NEW.complaint_id = '' THEN
        NEW.complaint_id := 'C-' || LPAD((SELECT COALESCE(MAX(CAST(SUBSTRING(complaint_id FROM 3) AS INT)), 0) + 1 FROM complaints)::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_complaint_id ON complaints;
CREATE TRIGGER set_complaint_id BEFORE INSERT ON complaints
    FOR EACH ROW EXECUTE FUNCTION generate_complaint_id();

-- Auto-generate task_id (T-0001, T-0002, ...)
CREATE OR REPLACE FUNCTION generate_task_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.task_id IS NULL OR NEW.task_id = '' THEN
        NEW.task_id := 'T-' || LPAD((SELECT COALESCE(MAX(CAST(SUBSTRING(task_id FROM 3) AS INT)), 0) + 1 FROM maintenance_tasks)::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_task_id ON maintenance_tasks;
CREATE TRIGGER set_task_id BEFORE INSERT ON maintenance_tasks
    FOR EACH ROW EXECUTE FUNCTION generate_task_id();

-- Auto-generate block_id (B-0001, B-0002, ...)
CREATE OR REPLACE FUNCTION generate_block_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.block_id IS NULL OR NEW.block_id = '' THEN
        NEW.block_id := 'B-' || LPAD((SELECT COALESCE(MAX(CAST(SUBSTRING(block_id FROM 3) AS INT)), 0) + 1 FROM maintenance_blocks)::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_block_id ON maintenance_blocks;
CREATE TRIGGER set_block_id BEFORE INSERT ON maintenance_blocks
    FOR EACH ROW EXECUTE FUNCTION generate_block_id();

-- Auto-generate team_id (TEAM-0001, TEAM-0002, ...)
CREATE OR REPLACE FUNCTION generate_team_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.team_id IS NULL OR NEW.team_id = '' THEN
        NEW.team_id := 'TEAM-' || LPAD((SELECT COALESCE(MAX(CAST(SUBSTRING(team_id FROM 6) AS INT)), 0) + 1 FROM maintenance_teams)::TEXT, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: maintenance_teams already has team_id populated from seed data
-- This trigger will fire for any future inserts without team_id


-- =============================================================
-- PART 2: Auto-update updated_at timestamps
-- =============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_asset_registry_updated_at ON asset_registry;
CREATE TRIGGER update_asset_registry_updated_at BEFORE UPDATE ON asset_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_complaints_updated_at ON complaints;
CREATE TRIGGER update_complaints_updated_at BEFORE UPDATE ON complaints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_maintenance_tasks_updated_at ON maintenance_tasks;
CREATE TRIGGER update_maintenance_tasks_updated_at BEFORE UPDATE ON maintenance_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_maintenance_teams_updated_at ON maintenance_teams;
CREATE TRIGGER update_maintenance_teams_updated_at BEFORE UPDATE ON maintenance_teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_maintenance_blocks_updated_at ON maintenance_blocks;
CREATE TRIGGER update_maintenance_blocks_updated_at BEFORE UPDATE ON maintenance_blocks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================
-- PART 3: Workflow status change tracking
-- =============================================================

CREATE OR REPLACE FUNCTION record_workflow_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO workflow_status_history (task_id, complaint_id, previous_status, new_status, changed_by_user_id)
        VALUES (NEW.task_id, NEW.complaint_id, OLD.status, NEW.status, NULL);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS track_maintenance_task_status_change ON maintenance_tasks;
CREATE TRIGGER track_maintenance_task_status_change
    AFTER UPDATE ON maintenance_tasks
    FOR EACH ROW EXECUTE FUNCTION record_workflow_status_change();


-- =============================================================
-- PART 4: Indexes
-- =============================================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_department ON users(department);
CREATE INDEX IF NOT EXISTS idx_users_section ON users(section_id);
CREATE INDEX IF NOT EXISTS idx_users_supabase_id ON users(supabase_user_id);

-- Asset registry
CREATE INDEX IF NOT EXISTS idx_asset_registry_section ON asset_registry(section_id);
CREATE INDEX IF NOT EXISTS idx_asset_registry_department ON asset_registry(department);
CREATE INDEX IF NOT EXISTS idx_asset_registry_overdue ON asset_registry(is_overdue);
CREATE INDEX IF NOT EXISTS idx_asset_registry_criticality ON asset_registry(asset_criticality);
CREATE INDEX IF NOT EXISTS idx_asset_registry_asset_id ON asset_registry(asset_id);

-- Complaints
CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_reporter ON complaints(reporter_user_id);
CREATE INDEX IF NOT EXISTS idx_complaints_section ON complaints(section_id);
CREATE INDEX IF NOT EXISTS idx_complaints_asset ON complaints(asset_id);
CREATE INDEX IF NOT EXISTS idx_complaints_created ON complaints(created_at DESC);

-- Maintenance tasks
CREATE INDEX IF NOT EXISTS idx_maint_tasks_status ON maintenance_tasks(status);
CREATE INDEX IF NOT EXISTS idx_maint_tasks_priority ON maintenance_tasks(priority);
CREATE INDEX IF NOT EXISTS idx_maint_tasks_section ON maintenance_tasks(section_id);
CREATE INDEX IF NOT EXISTS idx_maint_tasks_team ON maintenance_tasks(assigned_team_id);
CREATE INDEX IF NOT EXISTS idx_maint_tasks_complaint ON maintenance_tasks(complaint_id);

-- Maintenance teams
CREATE INDEX IF NOT EXISTS idx_maint_teams_department ON maintenance_teams(department);
CREATE INDEX IF NOT EXISTS idx_maint_teams_section ON maintenance_teams(section_id);
CREATE INDEX IF NOT EXISTS idx_maint_teams_status ON maintenance_teams(status);

-- Maintenance blocks
CREATE INDEX IF NOT EXISTS idx_maint_blocks_section ON maintenance_blocks(section_id);
CREATE INDEX IF NOT EXISTS idx_maint_blocks_approval ON maintenance_blocks(approval_status);

-- Dashboard alerts
CREATE INDEX IF NOT EXISTS idx_alerts_user ON dashboard_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_read ON dashboard_alerts(is_read);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON dashboard_alerts(created_at DESC);

-- Audit events
CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at DESC);

-- AI classifications
CREATE INDEX IF NOT EXISTS idx_ai_class_complaint ON ai_classifications(complaint_id);

-- Inspector verifications
CREATE INDEX IF NOT EXISTS idx_insp_verif_complaint ON inspector_verifications(complaint_id);

-- Workflow history
CREATE INDEX IF NOT EXISTS idx_workflow_history_task ON workflow_status_history(task_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_complaint ON workflow_status_history(complaint_id);
CREATE INDEX IF NOT EXISTS idx_workflow_history_changed ON workflow_status_history(changed_at DESC);


-- =============================================================
-- PART 5: Row Level Security (RLS) Policies
-- =============================================================

-- Enable RLS on all tables (safe to run multiple times)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE asset_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_blocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_classifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE inspector_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_status_history ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid conflicts
DO $$
DECLARE
    pol RECORD;
BEGIN
    FOR pol IN SELECT policyname, tablename FROM pg_policies WHERE schemaname = 'public' LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol.policyname, pol.tablename);
    END LOOP;
END $$;

-- === USERS ===
CREATE POLICY users_read_own ON users FOR SELECT
    USING (supabase_user_id = auth.uid());

CREATE POLICY users_admin_read_all ON users FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Administrator')
    );

CREATE POLICY users_manager_read_all ON users FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Maintenance_Manager')
    );

CREATE POLICY users_update_own ON users FOR UPDATE
    USING (supabase_user_id = auth.uid());

CREATE POLICY users_admin_insert ON users FOR INSERT
    WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Administrator')
    );

CREATE POLICY users_admin_delete ON users FOR DELETE
    USING (
        EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Administrator')
    );

-- === ASSET_REGISTRY ===
CREATE POLICY asset_read_all ON asset_registry FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY asset_manager_write ON asset_registry FOR ALL
    USING (
        EXISTS (SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role IN ('Maintenance_Manager', 'Administrator'))
    );

-- === COMPLAINTS ===
CREATE POLICY complaints_read_own ON complaints FOR SELECT
    USING (
        reporter_user_id = (SELECT id FROM users WHERE supabase_user_id = auth.uid())
    );

CREATE POLICY complaints_read_manager ON complaints FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Inspector', 'Administrator')
        )
    );

CREATE POLICY complaints_insert_own ON complaints FOR INSERT
    WITH CHECK (
        reporter_user_id = (SELECT id FROM users WHERE supabase_user_id = auth.uid())
    );

CREATE POLICY complaints_update_inspector ON complaints FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Inspector', 'Maintenance_Manager', 'Administrator')
        )
    );

-- === MAINTENANCE_TASKS ===
CREATE POLICY tasks_read_manager ON maintenance_tasks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator', 'Inspector')
        )
    );

CREATE POLICY tasks_read_assigned_team ON maintenance_tasks FOR SELECT
    USING (
        assigned_team_id IN (
            SELECT id FROM maintenance_teams
            WHERE team_lead_user_id = (SELECT id FROM users WHERE supabase_user_id = auth.uid())
        )
    );

CREATE POLICY tasks_read_staff ON maintenance_tasks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role = 'Maintenance_Staff'
        )
    );

CREATE POLICY tasks_update_manager ON maintenance_tasks FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

CREATE POLICY tasks_insert_manager ON maintenance_tasks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

-- === MAINTENANCE_TEAMS ===
CREATE POLICY teams_read_all ON maintenance_teams FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY teams_update_manager ON maintenance_teams FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

CREATE POLICY teams_insert_manager ON maintenance_teams FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

-- === MAINTENANCE_BLOCKS ===
CREATE POLICY blocks_read_all ON maintenance_blocks FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY blocks_update_manager ON maintenance_blocks FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

CREATE POLICY blocks_insert_manager ON maintenance_blocks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

-- === AI_CLASSIFICATIONS ===
CREATE POLICY ai_read_all ON ai_classifications FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY ai_insert_system ON ai_classifications FOR INSERT
    WITH CHECK (true);

-- === INSPECTOR_VERIFICATIONS ===
CREATE POLICY verif_read_all ON inspector_verifications FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY verif_insert_inspector ON inspector_verifications FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Inspector'
        )
    );

CREATE POLICY verif_update_inspector ON inspector_verifications FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Inspector'
        )
    );

-- === DASHBOARD_ALERTS ===
CREATE POLICY alerts_read_own ON dashboard_alerts FOR SELECT
    USING (
        user_id = (SELECT id FROM users WHERE supabase_user_id = auth.uid())
    );

CREATE POLICY alerts_read_admin ON dashboard_alerts FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid() AND role = 'Administrator'
        )
    );

CREATE POLICY alerts_insert_system ON dashboard_alerts FOR INSERT
    WITH CHECK (true);

CREATE POLICY alerts_update_own ON dashboard_alerts FOR UPDATE
    USING (
        user_id = (SELECT id FROM users WHERE supabase_user_id = auth.uid())
    );

-- === AUDIT_EVENTS ===
CREATE POLICY audit_read_manager ON audit_events FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users WHERE supabase_user_id = auth.uid()
            AND role IN ('Maintenance_Manager', 'Administrator')
        )
    );

CREATE POLICY audit_insert_system ON audit_events FOR INSERT
    WITH CHECK (true);

-- === WORKFLOW_STATUS_HISTORY ===
CREATE POLICY workflow_read_all ON workflow_status_history FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY workflow_insert_system ON workflow_status_history FOR INSERT
    WITH CHECK (true);


-- =============================================================
-- PART 6: Seed data for empty tables
-- =============================================================

-- === Sample complaints ===
INSERT INTO complaints (complaint_id, reporter_user_id, state, city, section_id, asset_type, asset_id, description, status)
VALUES
    ('C-0001',
     (SELECT id FROM users WHERE email = 'reporter1@railmaintain.in'),
     'Maharashtra', 'Mumbai', 'S-02', 'Signal',
     (SELECT asset_id FROM asset_registry WHERE asset_id = 'SIG-S02-04'),
     'Signal SN-4 showing red aspect continuously for 3 hours. Trains are stuck at Dadar station. Possible bulb failure or power supply issue in the signal circuit.',
     'Reported'),

    ('C-0002',
     (SELECT id FROM users WHERE email = 'reporter2@railmaintain.in'),
     'Maharashtra', 'Mumbai', 'S-01', 'Track',
     (SELECT asset_id FROM asset_registry WHERE asset_id = 'TRK-S01-12'),
     'Visible gap detected between rail joints near KM 45.2. Alignment seems off by 3mm. Potential risk of derailment if not addressed.',
     'Reported'),

    ('C-0003',
     (SELECT id FROM users WHERE email = 'reporter1@railmaintain.in'),
     'Maharashtra', 'Mumbai', 'S-02', 'Electrical Equipment',
     (SELECT asset_id FROM asset_registry WHERE asset_id = 'ELEC-S02-07'),
     'Transformer making unusual humming noise and showing temperature reading of 95°C. Normal operating temperature is 70°C. Risk of transformer failure.',
     'Reported');


-- === Sample AI classifications ===
INSERT INTO ai_classifications (complaint_id, department, fault_category, severity, base_priority, confidence, requires_human_review, model_version)
VALUES
    ('C-0001', 'Signalling', 'Signal Failure', 'High', 'High', 0.92, false, 'v1.0'),
    ('C-0002', 'Track', 'Rail Joint Defect', 'Critical', 'Critical', 0.88, true, 'v1.0'),
    ('C-0003', 'Electrical', 'Overheating Transformer', 'High', 'High', 0.85, true, 'v1.0');


-- === Sample maintenance tasks ===
INSERT INTO maintenance_tasks (task_id, complaint_id, asset_id, section_id, department, priority, status, assigned_team_id)
VALUES
    ('T-0001',
     'C-0001',
     (SELECT asset_id FROM asset_registry WHERE asset_id = 'SIG-S02-04'),
     'S-02', 'Signalling', 'High', 'Work_Scheduled',
     (SELECT id FROM maintenance_teams WHERE team_id = 'TEAM-001')),

    ('T-0002',
     'C-0002',
     (SELECT asset_id FROM asset_registry WHERE asset_id = 'TRK-S01-12'),
     'S-01', 'Track', 'Critical', 'Awaiting_Approval', NULL),

    ('T-0003',
     'C-0003',
     (SELECT asset_id FROM asset_registry WHERE asset_id = 'ELEC-S02-07'),
     'S-02', 'Electrical', 'High', 'Awaiting_Approval', NULL);


-- === Sample maintenance blocks ===
INSERT INTO maintenance_blocks (block_id, section_id, start_time, end_time, combined_tasks, grouping_status, safety_buffer_minutes, approval_status)
VALUES
    ('B-0001',
     'S-02',
     '2026-09-01T02:00:00+00:00',
     '2026-09-01T06:00:00+00:00',
     ARRAY['T-0001'],
     'Recommended Bundle',
     15,
     'Pending'),

    ('B-0002',
     'S-01',
     '2026-09-02T01:00:00+00:00',
     '2026-09-02T05:00:00+00:00',
     ARRAY['T-0002'],
     'Recommended Bundle',
     30,
     'Pending');


-- === Sample dashboard alerts ===
INSERT INTO dashboard_alerts (user_id, alert_type, title, message, resource_type, resource_id, priority, is_read)
VALUES
    ((SELECT id FROM users WHERE email = 'admin@railmaintain.in'),
     'CRITICAL_COMPLAINT', 'Critical Track Defect Reported',
     'Rail joint gap detected near KM 45.2 on Section S-01. Potential derailment risk. Immediate inspection required.',
     'complaint', 'C-0002', 'Critical', false),

    ((SELECT id FROM users WHERE email = 'manager.signal@railmaintain.in'),
     'APPROVAL_PENDING', 'Block Approval Required',
     'Maintenance block B-0001 for Signalling Team Alpha needs approval. Scheduled for 2026-09-01 02:00-06:00 IST.',
     'maintenance_block', 'B-0001', 'High', false),

    ((SELECT id FROM users WHERE email = 'admin@railmaintain.in'),
     'OVERDUE_MAINTENANCE', 'Overdue Asset Maintenance',
     'Asset SIG-S02-04 (Signal head) is overdue for maintenance. Last maintained: 2026-02-23. Next due: 2026-08-22.',
     'asset', 'SIG-S02-04', 'High', false),

    ((SELECT id FROM users WHERE email = 'manager.track@railmaintain.in'),
     'APPROVAL_PENDING', 'Block Approval Required',
     'Maintenance block B-0002 for Track Team Alpha needs approval. Scheduled for 2026-09-02 01:00-05:00 IST.',
     'maintenance_block', 'B-0002', 'High', false);


-- === Sample audit events ===
INSERT INTO audit_events (actor_user_id, action, resource_type, resource_id, status, details)
VALUES
    ((SELECT id FROM users WHERE email = 'admin@railmaintain.in'),
     'LOGIN', 'session', NULL, 'success', '{"ip": "192.168.1.1"}'),

    ((SELECT id FROM users WHERE email = 'reporter1@railmaintain.in'),
     'COMPLAINT_CREATED', 'complaint', 'C-0001', 'success', '{"description": "Signal failure reported"}'),

    ((SELECT id FROM users WHERE email = 'reporter2@railmaintain.in'),
     'COMPLAINT_CREATED', 'complaint', 'C-0002', 'success', '{"description": "Track defect reported"}'),

    ((SELECT id FROM users WHERE email = 'reporter1@railmaintain.in'),
     'COMPLAINT_CREATED', 'complaint', 'C-0003', 'success', '{"description": "Transformer overheating reported"}');


-- === Sample workflow status history ===
INSERT INTO workflow_status_history (task_id, complaint_id, previous_status, new_status, reason)
VALUES
    ('T-0001', 'C-0001', NULL, 'Reported', 'Complaint received'),
    ('T-0001', 'C-0001', 'Reported', 'Classified', 'AI classification completed'),
    ('T-0001', 'C-0001', 'Classified', 'Awaiting_Approval', 'Task created, awaiting block approval'),
    ('T-0001', 'C-0001', 'Awaiting_Approval', 'Work_Scheduled', 'Block approved, work scheduled'),

    ('T-0002', 'C-0002', NULL, 'Reported', 'Complaint received'),
    ('T-0002', 'C-0002', 'Reported', 'Classified', 'AI classification completed (requires human review)'),

    ('T-0003', 'C-0003', NULL, 'Reported', 'Complaint received'),
    ('T-0003', 'C-0003', 'Reported', 'Classified', 'AI classification completed (requires human review)');


-- =============================================================
-- PART 7: Storage Buckets
-- =============================================================

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
    ('complaint-photos', 'complaint-photos', false, 5242880, ARRAY['image/jpeg', 'image/png', 'image/gif']),
    ('inspection-photos', 'inspection-photos', false, 10485760, ARRAY['image/jpeg', 'image/png', 'image/gif']),
    ('work-completion-photos', 'work-completion-photos', false, 10485760, ARRAY['image/jpeg', 'image/png', 'image/gif'])
ON CONFLICT (id) DO NOTHING;

-- Storage policies for complaint-photos
CREATE POLICY complaint_photos_insert ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'complaint-photos');

CREATE POLICY complaint_photos_select ON storage.objects FOR SELECT TO authenticated
    USING (bucket_id = 'complaint-photos');

-- Storage policies for inspection-photos
CREATE POLICY inspection_photos_insert ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'inspection-photos');

CREATE POLICY inspection_photos_select ON storage.objects FOR SELECT TO authenticated
    USING (bucket_id = 'inspection-photos');

-- Storage policies for work-completion-photos
CREATE POLICY completion_photos_insert ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (bucket_id = 'work-completion-photos');

CREATE POLICY completion_photos_select ON storage.objects FOR SELECT TO authenticated
    USING (bucket_id = 'work-completion-photos');


-- =============================================================
-- PART 8: Enable Realtime
-- =============================================================

-- Enable realtime on key tables
ALTER PUBLICATION supabase_realtime ADD TABLE dashboard_alerts;
ALTER PUBLICATION supabase_realtime ADD TABLE maintenance_tasks;
ALTER PUBLICATION supabase_realtime ADD TABLE complaints;
ALTER PUBLICATION supabase_realtime ADD TABLE maintenance_blocks;


-- =============================================================
-- VERIFICATION
-- =============================================================

-- Check all tables
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Check row counts
SELECT 'users' AS tbl, COUNT(*) AS rows FROM users
UNION ALL SELECT 'asset_registry', COUNT(*) FROM asset_registry
UNION ALL SELECT 'complaints', COUNT(*) FROM complaints
UNION ALL SELECT 'maintenance_tasks', COUNT(*) FROM maintenance_tasks
UNION ALL SELECT 'maintenance_teams', COUNT(*) FROM maintenance_teams
UNION ALL SELECT 'maintenance_blocks', COUNT(*) FROM maintenance_blocks
UNION ALL SELECT 'ai_classifications', COUNT(*) FROM ai_classifications
UNION ALL SELECT 'inspector_verifications', COUNT(*) FROM inspector_verifications
UNION ALL SELECT 'dashboard_alerts', COUNT(*) FROM dashboard_alerts
UNION ALL SELECT 'audit_events', COUNT(*) FROM audit_events
UNION ALL SELECT 'workflow_status_history', COUNT(*) FROM workflow_status_history;

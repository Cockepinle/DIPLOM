from django.db import migrations


CREATE_SQL = """
-- FUNCTIONS
CREATE OR REPLACE FUNCTION fn_calc_course_completion_rate(p_course_id BIGINT)
RETURNS NUMERIC(5,2)
LANGUAGE plpgsql
AS $$
DECLARE
    total_count INTEGER;
    completed_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_count
    FROM courses_enrollment
    WHERE course_id = p_course_id;

    IF total_count = 0 THEN
        RETURN 0;
    END IF;

    SELECT COUNT(*) INTO completed_count
    FROM courses_enrollment
    WHERE course_id = p_course_id AND completed = TRUE;

    RETURN ROUND((completed_count::NUMERIC / total_count::NUMERIC) * 100, 2);
END;
$$;

CREATE OR REPLACE FUNCTION fn_employee_average_score(p_user_id BIGINT)
RETURNS NUMERIC(5,2)
LANGUAGE plpgsql
AS $$
DECLARE
    avg_score NUMERIC(5,2);
BEGIN
    SELECT ROUND(AVG(score)::NUMERIC, 2) INTO avg_score
    FROM results_testresult
    WHERE user_id = p_user_id AND score IS NOT NULL;

    RETURN COALESCE(avg_score, 0);
END;
$$;

-- PROCEDURES
CREATE OR REPLACE PROCEDURE sp_mark_overdue_enrollments()
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE courses_enrollment
    SET status = 'OVERDUE'
    WHERE due_date IS NOT NULL
      AND due_date < CURRENT_DATE
      AND completed = FALSE
      AND status IN ('ASSIGNED', 'IN_PROGRESS');
END;
$$;

CREATE OR REPLACE PROCEDURE sp_log_manual_event(
    p_user_id BIGINT,
    p_event_type VARCHAR(30),
    p_course_id BIGINT DEFAULT NULL,
    p_message TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO analytics_trainingevent(user_id, event_type, course_id, created_at, metadata)
    VALUES (
        p_user_id,
        p_event_type,
        p_course_id,
        NOW(),
        jsonb_build_object('source', 'procedure', 'message', COALESCE(p_message, ''))
    );

    INSERT INTO analytics_auditlog(actor_id, action, object_type, object_id, message, metadata, created_at)
    VALUES (
        p_user_id,
        'MANUAL_EVENT_LOGGED',
        'TrainingEvent',
        '',
        COALESCE(p_message, 'Manual event logged'),
        jsonb_build_object('event_type', p_event_type, 'course_id', p_course_id),
        NOW()
    );
END;
$$;

-- TRIGGERS
CREATE OR REPLACE FUNCTION trg_enrollment_status_sync_fn()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.completed = TRUE OR NEW.progress >= 100 THEN
        NEW.completed := TRUE;
        NEW.status := 'COMPLETED';
    ELSIF NEW.progress > 0 AND NEW.status = 'ASSIGNED' THEN
        NEW.status := 'IN_PROGRESS';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_enrollment_status_sync ON courses_enrollment;
CREATE TRIGGER trg_enrollment_status_sync
BEFORE UPDATE ON courses_enrollment
FOR EACH ROW
EXECUTE FUNCTION trg_enrollment_status_sync_fn();

CREATE OR REPLACE FUNCTION trg_testresult_audit_insert_fn()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO analytics_auditlog(actor_id, action, object_type, object_id, message, metadata, created_at)
    VALUES (
        NEW.user_id,
        'TEST_RESULT_CREATED',
        'TestResult',
        NEW.id::TEXT,
        'Создан новый результат теста',
        jsonb_build_object('test_id', NEW.test_id, 'status', NEW.status, 'score', NEW.score),
        NOW()
    );
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_testresult_audit_insert ON results_testresult;
CREATE TRIGGER trg_testresult_audit_insert
AFTER INSERT ON results_testresult
FOR EACH ROW
EXECUTE FUNCTION trg_testresult_audit_insert_fn();

-- VIEWS
CREATE OR REPLACE VIEW vw_course_progress_summary AS
SELECT
    c.id AS course_id,
    c.title AS course_title,
    COUNT(e.id) AS total_enrollments,
    COUNT(*) FILTER (WHERE e.completed = TRUE) AS completed_enrollments,
    COUNT(*) FILTER (WHERE e.status = 'OVERDUE') AS overdue_enrollments,
    fn_calc_course_completion_rate(c.id) AS completion_rate
FROM courses_course c
LEFT JOIN courses_enrollment e ON e.course_id = c.id
GROUP BY c.id, c.title;

CREATE OR REPLACE VIEW vw_employee_performance_summary AS
SELECT
    u.id AS user_id,
    u.email AS email,
    COUNT(DISTINCT e.course_id) AS assigned_courses,
    COUNT(DISTINCT e.course_id) FILTER (WHERE e.completed = TRUE) AS completed_courses,
    fn_employee_average_score(u.id) AS avg_test_score,
    COUNT(tr.id) AS total_test_attempts
FROM users_user u
LEFT JOIN courses_enrollment e ON e.user_id = u.id
LEFT JOIN results_testresult tr ON tr.user_id = u.id
WHERE u.role = 'EMPLOYEE'
GROUP BY u.id, u.email;
"""


DROP_SQL = """
DROP VIEW IF EXISTS vw_employee_performance_summary;
DROP VIEW IF EXISTS vw_course_progress_summary;

DROP TRIGGER IF EXISTS trg_testresult_audit_insert ON results_testresult;
DROP FUNCTION IF EXISTS trg_testresult_audit_insert_fn();

DROP TRIGGER IF EXISTS trg_enrollment_status_sync ON courses_enrollment;
DROP FUNCTION IF EXISTS trg_enrollment_status_sync_fn();

DROP PROCEDURE IF EXISTS sp_log_manual_event(BIGINT, VARCHAR, BIGINT, TEXT);
DROP PROCEDURE IF EXISTS sp_mark_overdue_enrollments();

DROP FUNCTION IF EXISTS fn_employee_average_score(BIGINT);
DROP FUNCTION IF EXISTS fn_calc_course_completion_rate(BIGINT);
"""


def create_db_objects(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(CREATE_SQL)


def drop_db_objects(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(DROP_SQL)


class Migration(migrations.Migration):
    dependencies = [
        ('analytics', '0002_remove_trainingevent_program_and_event_types'),
    ]

    operations = [
        migrations.RunPython(create_db_objects, drop_db_objects),
    ]


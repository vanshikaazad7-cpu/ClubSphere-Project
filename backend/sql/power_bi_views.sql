-- ==============================================================================
-- ClubSphere — Optimized SQL Views for Power BI Reporting & Institutional Analytics
-- System Design Document (SDD) Section 8.5 Implementation
-- ==============================================================================

-- 1. View: Event Registration Summary & Fill Rate
CREATE OR ALTER VIEW vw_EventRegistrationSummary AS
SELECT 
    e.EventId,
    e.Title AS EventTitle,
    e.ClubId,
    c.Name AS ClubName,
    d.Name AS DepartmentName,
    e.EventDate,
    e.RegistrationDeadline,
    e.Capacity,
    e.Status AS EventStatus,
    COUNT(CASE WHEN er.Status = 'confirmed' THEN 1 END) AS ConfirmedRegistrations,
    COUNT(CASE WHEN er.Status = 'waitlisted' THEN 1 END) AS WaitlistedRegistrations,
    COUNT(CASE WHEN er.Status = 'cancelled' THEN 1 END) AS CancelledRegistrations,
    CASE 
        WHEN e.Capacity - COUNT(CASE WHEN er.Status = 'confirmed' THEN 1 END) < 0 THEN 0
        ELSE e.Capacity - COUNT(CASE WHEN er.Status = 'confirmed' THEN 1 END)
    END AS SeatsLeft,
    CASE 
        WHEN e.Capacity > 0 THEN 
            ROUND((CAST(COUNT(CASE WHEN er.Status = 'confirmed' THEN 1 END) AS FLOAT) / e.Capacity) * 100, 2)
        ELSE 0.0
    END AS FillRatePercent
FROM Events e
INNER JOIN Clubs c ON e.ClubId = c.ClubId
INNER JOIN Departments d ON c.DepartmentId = d.DepartmentId
LEFT JOIN EventRegistrations er ON e.EventId = er.EventId
GROUP BY 
    e.EventId, e.Title, e.ClubId, c.Name, d.Name, e.EventDate, e.RegistrationDeadline, e.Capacity, e.Status;
GO

-- 2. View: Event Attendance Rate
CREATE OR ALTER VIEW vw_AttendanceRate AS
SELECT 
    e.EventId,
    e.Title AS EventTitle,
    c.ClubId,
    c.Name AS ClubName,
    e.EventDate,
    COUNT(DISTINCT er.UserId) AS ConfirmedRegistrations,
    COUNT(DISTINCT a.UserId) AS AttendedCount,
    CASE 
        WHEN COUNT(DISTINCT er.UserId) > 0 THEN 
            ROUND((CAST(COUNT(DISTINCT a.UserId) AS FLOAT) / COUNT(DISTINCT er.UserId)) * 100, 2)
        ELSE 0.0
    END AS AttendanceRatePercent
FROM Events e
INNER JOIN Clubs c ON e.ClubId = c.ClubId
LEFT JOIN EventRegistrations er ON e.EventId = er.EventId AND er.Status = 'confirmed'
LEFT JOIN Attendance a ON e.EventId = a.EventId
GROUP BY 
    e.EventId, e.Title, c.ClubId, c.Name, e.EventDate;
GO

-- 3. View: Club Activity & Health Metrics
CREATE OR ALTER VIEW vw_ClubActivity AS
SELECT 
    c.ClubId,
    c.Name AS ClubName,
    d.DepartmentId,
    d.Name AS DepartmentName,
    u.FullName AS ManagerName,
    c.Status AS ClubStatus,
    c.CreatedAt AS ClubCreatedDate,
    COUNT(DISTINCT cm.UserId) AS ActiveMembersCount,
    COUNT(DISTINCT e.EventId) AS TotalEventsHosted,
    COUNT(DISTINCT CASE WHEN e.Status = 'published' THEN e.EventId END) AS PublishedEvents,
    COUNT(DISTINCT CASE WHEN e.Status = 'completed' THEN e.EventId END) AS CompletedEvents
FROM Clubs c
INNER JOIN Departments d ON c.DepartmentId = d.DepartmentId
INNER JOIN Users u ON c.ManagerUserId = u.UserId
LEFT JOIN ClubMemberships cm ON c.ClubId = cm.ClubId AND cm.Status = 'active'
LEFT JOIN Events e ON c.ClubId = e.ClubId
GROUP BY 
    c.ClubId, c.Name, d.DepartmentId, d.Name, u.FullName, c.Status, c.CreatedAt;
GO

-- 4. View: Department Student Participation
CREATE OR ALTER VIEW vw_DepartmentParticipation AS
SELECT 
    d.DepartmentId,
    d.Name AS DepartmentName,
    FORMAT(er.RegisteredAt, 'yyyy-MM') AS RegistrationYearMonth,
    COUNT(DISTINCT er.UserId) AS UniqueStudentParticipants,
    COUNT(er.RegistrationId) AS TotalRegistrationCount
FROM EventRegistrations er
INNER JOIN Users u ON er.UserId = u.UserId
INNER JOIN Departments d ON u.DepartmentId = d.DepartmentId
WHERE er.Status = 'confirmed'
GROUP BY 
    d.DepartmentId, d.Name, FORMAT(er.RegisteredAt, 'yyyy-MM');
GO

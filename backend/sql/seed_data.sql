-- ==============================================================================
-- ClubSphere — Synthetic Demonstration Seed Data
-- Fictitious demo identities with @univ.edu test domain
-- Default password for all demo accounts: Test@1234
-- Bcrypt Hash: $2b$12$e8xM4bJ8oBwN4vUqI7iYveJg1P1tI1q6xP0eE.N5e7cT2N1W8O7qy (or test-generated)
-- ==============================================================================

-- 1. Seed Roles
SET IDENTITY_INSERT Roles ON;
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = 'Student')
    INSERT INTO Roles (RoleId, RoleName) VALUES (1, 'Student');
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = 'Club Manager')
    INSERT INTO Roles (RoleId, RoleName) VALUES (2, 'Club Manager');
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = 'Faculty')
    INSERT INTO Roles (RoleId, RoleName) VALUES (3, 'Faculty');
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = 'HOD')
    INSERT INTO Roles (RoleId, RoleName) VALUES (4, 'HOD');
IF NOT EXISTS (SELECT 1 FROM Roles WHERE RoleName = 'Administrator')
    INSERT INTO Roles (RoleId, RoleName) VALUES (5, 'Administrator');
SET IDENTITY_INSERT Roles OFF;

-- 2. Seed Departments
SET IDENTITY_INSERT Departments ON;
IF NOT EXISTS (SELECT 1 FROM Departments WHERE Code = 'CSE')
    INSERT INTO Departments (DepartmentId, Name, Code) VALUES (1, 'Computer Science & Engineering', 'CSE');
IF NOT EXISTS (SELECT 1 FROM Departments WHERE Code = 'ECE')
    INSERT INTO Departments (DepartmentId, Name, Code) VALUES (2, 'Electronics & Communication', 'ECE');
IF NOT EXISTS (SELECT 1 FROM Departments WHERE Code = 'MECH')
    INSERT INTO Departments (DepartmentId, Name, Code) VALUES (3, 'Mechanical Engineering', 'MECH');
IF NOT EXISTS (SELECT 1 FROM Departments WHERE Code = 'GEN')
    INSERT INTO Departments (DepartmentId, Name, Code) VALUES (4, 'University General Activities', 'GEN');
SET IDENTITY_INSERT Departments OFF;

-- 3. Seed Demo Users (Password: Test@1234)
-- Note: Replace password hashes with backend bcrypt verified hashes
SET IDENTITY_INSERT Users ON;
IF NOT EXISTS (SELECT 1 FROM Users WHERE Email = 'admin@univ.edu')
    INSERT INTO Users (UserId, Email, PasswordHash, FullName, RoleId, DepartmentId, IsActive)
    VALUES (1, 'admin@univ.edu', '$2b$12$Z0bWq0sWq47m8rWfFm7q4e0tF2cT3h5o6j7k8l9m0n1o2p3q4r5s6', 'System Administrator', 5, 4, 1);

IF NOT EXISTS (SELECT 1 FROM Users WHERE Email = 'hod@univ.edu')
    INSERT INTO Users (UserId, Email, PasswordHash, FullName, RoleId, DepartmentId, IsActive)
    VALUES (2, 'hod@univ.edu', '$2b$12$Z0bWq0sWq47m8rWfFm7q4e0tF2cT3h5o6j7k8l9m0n1o2p3q4r5s6', 'Dr. Ramesh Kumar (HOD)', 4, 1, 1);

IF NOT EXISTS (SELECT 1 FROM Users WHERE Email = 'faculty@univ.edu')
    INSERT INTO Users (UserId, Email, PasswordHash, FullName, RoleId, DepartmentId, IsActive)
    VALUES (3, 'faculty@univ.edu', '$2b$12$Z0bWq0sWq47m8rWfFm7q4e0tF2cT3h5o6j7k8l9m0n1o2p3q4r5s6', 'Prof. Sunita Sharma', 3, 1, 1);

IF NOT EXISTS (SELECT 1 FROM Users WHERE Email = 'manager@univ.edu')
    INSERT INTO Users (UserId, Email, PasswordHash, FullName, RoleId, DepartmentId, IsActive)
    VALUES (4, 'manager@univ.edu', '$2b$12$Z0bWq0sWq47m8rWfFm7q4e0tF2cT3h5o6j7k8l9m0n1o2p3q4r5s6', 'Aryan Sharma (Club Lead)', 2, 1, 1);

IF NOT EXISTS (SELECT 1 FROM Users WHERE Email = 'student@univ.edu')
    INSERT INTO Users (UserId, Email, PasswordHash, FullName, RoleId, DepartmentId, IsActive)
    VALUES (5, 'student@univ.edu', '$2b$12$Z0bWq0sWq47m8rWfFm7q4e0tF2cT3h5o6j7k8l9m0n1o2p3q4r5s6', 'Vanshika Azad', 1, 1, 1);
SET IDENTITY_INSERT Users OFF;

-- 4. Seed Clubs
SET IDENTITY_INSERT Clubs ON;
IF NOT EXISTS (SELECT 1 FROM Clubs WHERE Name = 'Robotics & Automation Society')
    INSERT INTO Clubs (ClubId, Name, DepartmentId, ManagerUserId, Description, Status)
    VALUES (1, 'Robotics & Automation Society', 1, 4, 'Designing autonomous drones, rovers, and competitive robotics projects.', 'active');
SET IDENTITY_INSERT Clubs OFF;

-- 5. Seed Events
SET IDENTITY_INSERT Events ON;
IF NOT EXISTS (SELECT 1 FROM Events WHERE Title = 'Annual AI & Robotics Hackathon 2026')
    INSERT INTO Events (EventId, ClubId, Title, VenueText, EventDate, RegistrationDeadline, Capacity, Status, CreatedByUserId)
    VALUES (1, 1, 'Annual AI & Robotics Hackathon 2026', 'Auditorium Hall A', '2026-10-25 10:00:00', '2026-10-24 18:00:00', 100, 'published', 4);
SET IDENTITY_INSERT Events OFF;

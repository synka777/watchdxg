-- 1. Create the trigger function
CREATE OR REPLACE FUNCTION update_last_updated_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.last_updated = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Drop the trigger if it already exists
DROP TRIGGER IF EXISTS set_last_updated ON users;

-- 3. Create the trigger
CREATE TRIGGER set_last_updated
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_last_updated_column();
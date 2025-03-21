from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List, Annotated
from enum import Enum
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import uuid
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Boolean, Enum as SQLAlchemyEnum, text
from sqlalchemy.ext.asyncio import async_sessionmaker

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
parsed_url = urlparse(DATABASE_URL)

# Database setup
engine = create_async_engine(
    f"postgresql+asyncpg://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}{parsed_url.path}?ssl=require",
    echo=True
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # Use environment variable in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# Role enumeration 
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    MANAGER = "manager"
    TEAM_HEAD = "team_head"
    MEMBER = "member"

# SQLAlchemy User model - using proper Enum type
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    # Use SQLAlchemyEnum to match the database enum type
    role = Column(SQLAlchemyEnum(UserRole, name="userrole"))
    disabled = Column(Boolean, default=False)

# Pydantic models
class UserBase(BaseModel):
    username: str
    email: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    disabled: bool = False
    
    class Config:
        from_attributes = True  # Updated from orm_mode in pydantic v2

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    stmt = text("SELECT * FROM users WHERE id = :user_id")
    result = await db.execute(stmt, {"user_id": user_id})
    user = result.fetchone()
    
    if user is None:
        raise credentials_exception
    
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        disabled=user.disabled
    )

def check_create_permission(creator_role: UserRole, target_role: UserRole) -> bool:
    role_hierarchy = {
        UserRole.SUPER_ADMIN: [UserRole.SUPER_ADMIN, UserRole.MANAGER, UserRole.TEAM_HEAD, UserRole.MEMBER],
        UserRole.MANAGER: [UserRole.TEAM_HEAD, UserRole.MEMBER],
        UserRole.TEAM_HEAD: [UserRole.MEMBER],
        UserRole.MEMBER: []
    }
    return target_role in role_hierarchy[creator_role]

# Authentication endpoint
@app.post("/token", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Query for user with matching username
    stmt = text("SELECT * FROM users WHERE username = :username")
    result = await db.execute(stmt, {"username": form_data.username})
    user = result.fetchone()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

# User management endpoints
@app.post("/users/", response_model=User)
async def create_user(
    user: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if not check_create_permission(current_user.role, user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with role {current_user.role} cannot create user with role {user.role}"
        )
    
    # Check if username or email already exists
    stmt = text("SELECT * FROM users WHERE username = :username OR email = :email")
    result = await db.execute(stmt, {"username": user.username, "email": user.email})
    if result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    # Insert user directly using SQL
    stmt = text("""
        INSERT INTO users (id, username, email, password, role, disabled)
        VALUES (:id, :username, :email, :password, :role, :disabled)
    """)
    await db.execute(stmt, {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "role": user.role.value,  # Use .value to convert enum to string
        "disabled": False
    })
    await db.commit()
    
    return User(
        id=user_id,
        username=user.username,
        email=user.email,
        role=user.role,
        disabled=False
    )

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/", response_model=List[User])
async def read_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view all users"
        )
    
    stmt = text("SELECT * FROM users")
    result = await db.execute(stmt)
    users = result.fetchall()
    
    return [
        User(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            disabled=user.disabled
        )
        for user in users
    ]

# Define the schema verification and migration function
async def verify_and_update_schema():
    """Verify database schema and make necessary updates"""
    print("Starting database schema verification...")
    
    async with engine.begin() as conn:
        # 1. Check if the table exists at all
        check_table_sql = text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        result = await conn.execute(check_table_sql)
        table_exists = result.scalar()
        
        if not table_exists:
            print("Users table doesn't exist. Creating from scratch.")
            await conn.run_sync(Base.metadata.create_all)
            return  # Exit early since we created everything from scratch
        
        # 2. Check and create userrole enum if it doesn't exist
        check_enum_sql = text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'userrole'
            );
        """)
        result = await conn.execute(check_enum_sql)
        enum_exists = result.scalar()
        
        if not enum_exists:
            print("Creating userrole enum type")
            create_enum_sql = text("""
                CREATE TYPE userrole AS ENUM ('super_admin', 'manager', 'team_head', 'member');
            """)
            await conn.execute(create_enum_sql)
        else:
            # Verify enum values match our expectations
            check_enum_values_sql = text("""
                SELECT enumlabel FROM pg_enum 
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
                ORDER BY enumsortorder;
            """)
            result = await conn.execute(check_enum_values_sql)
            db_enum_values = [row[0] for row in result.fetchall()]
            expected_values = [role.value for role in UserRole]
            
            if set(db_enum_values) != set(expected_values):
                print(f"Enum values mismatch. DB values: {db_enum_values}, Expected: {expected_values}")
                print("WARNING: Enum values differ but won't be automatically updated as it could break existing data")
                print("Consider manual migration if this is intentional")
        
        # 3. Check each required column in the users table
        expected_columns = {
            'id': {'type': 'character varying', 'nullable': False},
            'username': {'type': 'character varying', 'nullable': True},
            'email': {'type': 'character varying', 'nullable': True},
            'password': {'type': 'character varying', 'nullable': True},
            'role': {'type': 'userrole', 'nullable': True},
            'disabled': {'type': 'boolean', 'nullable': True}
        }
        
        for column_name, specs in expected_columns.items():
            # Check if column exists
            check_column_sql = text(f"""
                SELECT data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = '{column_name}';
            """)
            result = await conn.execute(check_column_sql)
            column_info = result.fetchone()
            
            if not column_info:
                print(f"Column '{column_name}' missing. Adding it now.")
                
                # Determine the SQL to add the column based on its type
                if column_name == 'role':
                    add_column_sql = text(f"ALTER TABLE users ADD COLUMN {column_name} userrole;")
                elif column_name == 'disabled':
                    add_column_sql = text(f"ALTER TABLE users ADD COLUMN {column_name} boolean DEFAULT FALSE;")
                elif column_name == 'id':
                    add_column_sql = text(f"ALTER TABLE users ADD COLUMN {column_name} character varying PRIMARY KEY;")
                else:
                    add_column_sql = text(f"ALTER TABLE users ADD COLUMN {column_name} character varying;")
                
                await conn.execute(add_column_sql)
                print(f"Added column '{column_name}' to users table")
                
                # Add indexes for certain columns
                if column_name in ['username', 'email']:
                    index_name = f"ix_users_{column_name}"
                    create_index_sql = text(f"CREATE INDEX IF NOT EXISTS {index_name} ON users ({column_name});")
                    await conn.execute(create_index_sql)
                    print(f"Created index for '{column_name}'")
                    
                    # Add unique constraint
                    constraint_name = f"uq_users_{column_name}"
                    create_constraint_sql = text(f"ALTER TABLE users ADD CONSTRAINT {constraint_name} UNIQUE ({column_name});")
                    await conn.execute(create_constraint_sql)
                    print(f"Added unique constraint for '{column_name}'")
            else:
                data_type, is_nullable = column_info
                is_nullable = is_nullable == 'YES'
                
                # Check if actual column type matches expected type
                if data_type == 'USER-DEFINED' and column_name == 'role':
                    # For enum types, PostgreSQL reports them as USER-DEFINED
                    # Check if the column uses the right enum type
                    check_enum_column_sql = text(f"""
                        SELECT udt_name FROM information_schema.columns 
                        WHERE table_name = 'users' AND column_name = 'role';
                    """)
                    result = await conn.execute(check_enum_column_sql)
                    udt_name = result.scalar()
                    
                    if udt_name != 'userrole':
                        print(f"Column 'role' has wrong enum type: {udt_name}")
                        print("This requires manual migration due to potential data loss")
                elif data_type != specs['type'] or is_nullable != specs['nullable']:
                    print(f"Column '{column_name}' has different type/nullability than expected")
                    print(f"Expected: {specs['type']}, {specs['nullable']}, Actual: {data_type}, {is_nullable}")
                    print("This requires manual migration due to potential data loss")
        
        # 4. Check for indexes and constraints
        for column_name in ['username', 'email']:
            # Check for index
            check_index_sql = text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'users' AND indexname = 'ix_users_{column_name}'
                );
            """)
            result = await conn.execute(check_index_sql)
            index_exists = result.scalar()
            
            if not index_exists:
                index_name = f"ix_users_{column_name}"
                create_index_sql = text(f"CREATE INDEX IF NOT EXISTS {index_name} ON users ({column_name});")
                await conn.execute(create_index_sql)
                print(f"Created missing index for '{column_name}'")
            
            # Check for unique constraint
            check_constraint_sql = text(f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE table_name = 'users' AND constraint_name = 'uq_users_{column_name}'
                    AND constraint_type = 'UNIQUE'
                );
            """)
            result = await conn.execute(check_constraint_sql)
            constraint_exists = result.scalar()
            
            if not constraint_exists:
                # Check if there's already a unique constraint with a different name
                check_existing_constraint_sql = text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.constraint_column_usage
                        WHERE table_name = 'users' AND column_name = '{column_name}'
                        AND constraint_name LIKE '%\_users\_%' ESCAPE '\\'
                    );
                """)
                result = await conn.execute(check_existing_constraint_sql)
                has_existing_constraint = result.scalar()
                
                if not has_existing_constraint:
                    constraint_name = f"uq_users_{column_name}"
                    create_constraint_sql = text(f"ALTER TABLE users ADD CONSTRAINT {constraint_name} UNIQUE ({column_name});")
                    try:
                        await conn.execute(create_constraint_sql)
                        print(f"Added unique constraint for '{column_name}'")
                    except Exception as e:
                        print(f"Could not add unique constraint for '{column_name}': {e}")
                        print("This might be due to duplicate values in the column")
    
    print("Database schema verification completed")

# Database initialization and schema verification
@app.on_event("startup")
async def startup_event():
    # First verify and update the schema
    await verify_and_update_schema()
    
    # Then check for and create super admin if needed
    async with async_session_maker() as session:
        try:
            # First check if users table is empty or has no super admin
            check_admin_sql = text("SELECT COUNT(*) FROM users WHERE role = :role")
            try:
                result = await session.execute(check_admin_sql, {"role": UserRole.SUPER_ADMIN.value})
                admin_count = result.scalar()
            except Exception:
                # If the query fails, assume no admin exists
                admin_count = 0
            
            if admin_count == 0:
                # Create initial super admin
                user_id = str(uuid.uuid4())
                hashed_password = get_password_hash("superadmin123")
                
                stmt = text("""
                    INSERT INTO users (id, username, email, password, role, disabled)
                    VALUES (:id, :username, :email, :password, :role, :disabled)
                """)
                await session.execute(stmt, {
                    "id": user_id,
                    "username": "superadmin",
                    "email": "superadmin@example.com",
                    "password": hashed_password,
                    "role": UserRole.SUPER_ADMIN.value,
                    "disabled": False
                })
                await session.commit()
                print("Created super admin user")
        except Exception as e:
            print(f"Error during super admin creation: {e}")
            await session.rollback()
            raise

@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Project(Base):
    __tablename__="projects"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(500))
    folder_name: Mapped[str]=mapped_column(String(500),default="")
    relative_path: Mapped[str]=mapped_column(String(2000),default="")
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
    thumbnail_path: Mapped[str|None]=mapped_column(String(1000),nullable=True)
    notes: Mapped[str]=mapped_column(Text,default="")
    files=relationship("ModelFile",back_populates="project",cascade="all, delete-orphan")
    tags=relationship("Tag",secondary="project_tags",back_populates="projects")

class ModelFile(Base):
    __tablename__="files"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    project_id: Mapped[int]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"))
    filename: Mapped[str]=mapped_column(String(500))
    relative_path: Mapped[str]=mapped_column(String(2000))
    extension: Mapped[str]=mapped_column(String(20))
    sha256: Mapped[str]=mapped_column(String(64),index=True)
    file_size: Mapped[int]=mapped_column(Integer,default=0)
    modified_at: Mapped[datetime]=mapped_column(DateTime)
    weight_g: Mapped[float|None]=mapped_column(Float,nullable=True)
    print_time_seconds: Mapped[int|None]=mapped_column(Integer,nullable=True)
    volume_mm3: Mapped[float|None]=mapped_column(Float,nullable=True)
    width_mm: Mapped[float|None]=mapped_column(Float,nullable=True)
    height_mm: Mapped[float|None]=mapped_column(Float,nullable=True)
    depth_mm: Mapped[float|None]=mapped_column(Float,nullable=True)
    material: Mapped[str|None]=mapped_column(String(100),nullable=True)
    metadata_json: Mapped[str]=mapped_column(Text,default="{}")
    manual_weight: Mapped[bool]=mapped_column(Boolean,default=False)
    manual_time: Mapped[bool]=mapped_column(Boolean,default=False)
    manual_material: Mapped[bool]=mapped_column(Boolean,default=False)
    project=relationship("Project",back_populates="files")
    __table_args__=(UniqueConstraint("relative_path",name="uq_file_relpath"),)

class Tag(Base):
    __tablename__="tags"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(200),unique=True,index=True)
    projects=relationship("Project",secondary="project_tags",back_populates="tags")

class ProjectTag(Base):
    __tablename__="project_tags"
    project_id: Mapped[int]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),primary_key=True)
    tag_id: Mapped[int]=mapped_column(ForeignKey("tags.id",ondelete="CASCADE"),primary_key=True)

class Material(Base):
    __tablename__="materials"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(100),unique=True)
    spool_price: Mapped[float]=mapped_column(Float,default=0)
    spool_weight_g: Mapped[float]=mapped_column(Float,default=1000)
    density: Mapped[float]=mapped_column(Float,default=1.24)
    active: Mapped[bool]=mapped_column(Boolean,default=True)

class Printer(Base):
    __tablename__="printers"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(200),unique=True)
    manufacturer: Mapped[str]=mapped_column(String(200),default="")
    model: Mapped[str]=mapped_column(String(200),default="")
    purchase_price: Mapped[float]=mapped_column(Float,default=0)
    resource_hours: Mapped[float]=mapped_column(Float,default=5000)
    average_power_w: Mapped[float]=mapped_column(Float,default=80)
    idle_power_w: Mapped[float]=mapped_column(Float,default=0)
    preheat_power_w: Mapped[float]=mapped_column(Float,default=0)
    preheat_minutes: Mapped[float]=mapped_column(Float,default=0)
    maintenance_cost: Mapped[float]=mapped_column(Float,default=0)
    maintenance_resource_hours: Mapped[float]=mapped_column(Float,default=0)
    consumables_cost: Mapped[float]=mapped_column(Float,default=0)
    consumables_resource_hours: Mapped[float]=mapped_column(Float,default=0)
    active: Mapped[bool]=mapped_column(Boolean,default=True)

class CalculationProfile(Base):
    __tablename__="calculation_profiles"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    name: Mapped[str]=mapped_column(String(100),unique=True)
    type: Mapped[str]=mapped_column(String(30),unique=True)
    settings_json: Mapped[str]=mapped_column(Text,default="{}")

class Setting(Base):
    __tablename__="settings"
    key: Mapped[str]=mapped_column(String(200),primary_key=True)
    value: Mapped[str]=mapped_column(Text,default="")
    updated_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class CalculationHistory(Base):
    __tablename__="calculation_history"
    id: Mapped[int]=mapped_column(Integer,primary_key=True)
    project_id: Mapped[int|None]=mapped_column(Integer,nullable=True)
    client_type: Mapped[str]=mapped_column(String(30))
    material: Mapped[str]=mapped_column(String(100))
    weight_g: Mapped[float]=mapped_column(Float)
    print_time_seconds: Mapped[int]=mapped_column(Integer)
    quantity: Mapped[int]=mapped_column(Integer)
    mode: Mapped[str]=mapped_column(String(30))
    result_json: Mapped[str]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)

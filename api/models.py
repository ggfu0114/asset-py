

from sqlalchemy import Column, Integer, VARCHAR, TIMESTAMP, FLOAT
from api.base import BaseModel


class User(BaseModel):
    __tablename__ = 'user'

    def __repr__(self):
        return '<User {}:{} >'.format(self.uid, self.name)

    uid = Column('Uid', Integer, primary_key=True)
    email = Column('Email', VARCHAR(64))
    name = Column('Name', VARCHAR(64))
    gender = Column('Gender', VARCHAR(64))
    picture = Column('Picture', VARCHAR(256))
    line_id = Column('LineId', VARCHAR(64))

    _default_fields = [
        "uid", "email", "name", "gender", "picture", "line_id"
    ]
    _hidden_fields = []
    _readonly_fields = []


class MyAsset(BaseModel):
    __tablename__ = 'myasset'

    aid = Column('Aid', Integer, primary_key=True)
    uid = Column('Uid', Integer)
    asset_type = Column('AssetType', VARCHAR(64))
    asset_sub_type = Column('AssetSubType', VARCHAR(64))
    code = Column('Code', VARCHAR(64))
    amount = Column('Amount', FLOAT)
    label = Column('Label', VARCHAR(64))
    market = Column('Market', VARCHAR(64))

    _default_fields = [
        "aid", "uid", "asset_type", "asset_sub_type", "code", "amount", "label", "market"
    ]
    _hidden_fields = []
    _readonly_fields = []


class AssetValue(BaseModel):
    __tablename__ = 'asset_value'

    aid = Column('Aid', Integer, primary_key=True)
    value = Column('Value', FLOAT)
    updated_at = Column('UpdatedAt', TIMESTAMP)
    created_at = Column('CreatedAt', TIMESTAMP)

    _default_fields = [
        "aid", "value", "updated_at", "created_at"
    ]
    _hidden_fields = []
    _readonly_fields = []

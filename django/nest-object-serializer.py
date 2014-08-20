# -*- coding: utf-8 -*-
from rest_framework import serializers
from accounts.models import UserProfile, AModel, BModel, CModel, DModel
from rest_framework.parsers import JSONParser
from django.utils.translation import ugettext_lazy as _
from StringIO import StringIO
import json
import ast
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework.compat import smart_text

class UserProfileSerializer(serializers.ModelSerializer):
  owner = serializers.Field(source='owner.username')
  class Meta:
    model = UserProfile
    field = ('id','owner','job','age','gender','address','salary')

# 簡單地展示了多層物件的實作法.
# A
#   aname
#   B  ( 用pk 方式 serialize )
#     bname
#   C  ( 用完整細節 serialize )
#     cname
#   D  ( 用完整細節 serialize, 同時可以新增 )
#     cname

class DModelSerializer(serializers.ModelSerializer):
  class Meta:
    model = DModel
    field = ('pk', 'dname')

# 可以先看 CField
# DField 傳回詳細物件, 也可以回存詳細物件
class DField(serializers.RelatedField):
  read_only = False
  def to_native(self, value):
    return {"pk": value.pk, "dname": value.dname}

  def from_native(self, data):
    # for ajax / form 的差異
    if type(data)!=type({}):
      try: data = ast.literal_eval(data)
      except: raise ValidationError(self.error_messages["invalid"])
    # 如果物件已經存在就直接回傳不更新
    try: 
      dobj = self.queryset.get(pk=data["pk"])
      return dobj
    except: pass
    # 不存在的物件, 在這邊建立
    dobj = DModelSerializer(data=data)
    if not dobj.is_valid():
      raise ValidationError(self.error_messages["invalid"])
    dobj.object.save()
    return dobj.object
      

class CModelSerializer(serializers.ModelSerializer):
  class Meta:
    model = CModel
    field = ('pk', 'cname')

# 這裡展示了將 object list 完整值傳到 client 端, 
# 但寫回 server 時只取其 pk 來設定母物件的欄位內容的做法.
class CField(serializers.RelatedField):
  # 若為 read_only, 則沒有機會進到 from_native
  read_only = False
  # 使用 PrimaryKeyRelatedField 的 'does_not_exist' 欄位
  # 主要是為了 i18n 最佳化

  # 簡單的傳回一個可以變成字串的物件
  def to_native(self, value):
    return {"pk": value.pk, "cname": value.cname}

  # 理論上 to_native 去什麼, from_native 就回來什麼
  # 但 from_native 有時收到的是字串形式, 必須要自己還原成 dict
  # 若用 json.loads 來做會碰到單引號(python)雙引號(json)的問題
  # 所以使用 literal_eval
  def from_native(self, data):
    # 如果不是 dict, 那就是 unicode string, 需要 parse
    if type(data)!=type({}):
      try: data = ast.literal_eval(data)
      except: raise ValidationError(self.error_messages["invalid"])
    # 取得 pk, 找看物件有沒有
    try: cobj = self.queryset.get(pk=data["pk"])
    except:
      msg = serializers.PrimaryKeyRelatedField.default_error_messages['does_not_exist'] % smart_text(data["pk"])
      raise ValidationError(msg)
    # 傳回的物件列表會用來重建母物件
    # 若需要改動子物件，也可以在這邊實作
    return cobj

class BModelSerializer(serializers.ModelSerializer):
  class Meta:
    model = BModel
    field = ('bname')

class AModelSerializer(serializers.ModelSerializer):
  cobj = CField(many=True)
  dobj = DField(many=True)
  class Meta:
    model = AModel
    field = ('aname', 'bobj', 'cobj', 'dobj')

<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyDrawingHints="1" version="3.4.0-Madeira" simplifyLocal="1" maxScale="0" simplifyAlgorithm="0" hasScaleBasedVisibilityFlag="0" labelsEnabled="0" simplifyDrawingTol="1" minScale="1e+8" simplifyMaxScale="1" readOnly="0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 type="singleSymbol" enableorderby="0" forceraster="0" symbollevels="0">
    <symbols>
      <symbol type="fill" clip_to_extent="1" name="0" alpha="1">
        <layer enabled="1" class="SimpleLine" pass="0" locked="0">
          <prop v="square" k="capstyle"/>
          <prop v="5;2" k="customdash"/>
          <prop v="3x:0,0,0,0,0,0" k="customdash_map_unit_scale"/>
          <prop v="MM" k="customdash_unit"/>
          <prop v="0" k="draw_inside_polygon"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="196,235,255,255" k="line_color"/>
          <prop v="solid" k="line_style"/>
          <prop v="0.46" k="line_width"/>
          <prop v="MM" k="line_width_unit"/>
          <prop v="0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="0" k="use_custom_dash"/>
          <prop v="3x:0,0,0,0,0,0" k="width_map_unit_scale"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" value="" name="name"/>
              <Option name="properties"/>
              <Option type="QString" value="collection" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="dualview/previewExpressions" value="id_add"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Pie" attributeLegend="1">
    <DiagramCategory labelPlacementMethod="XHeight" penAlpha="255" backgroundColor="#ffffff" penWidth="0" sizeType="MM" backgroundAlpha="255" minimumSize="0" maxScaleDenominator="1e+8" barWidth="5" height="15" penColor="#000000" enabled="0" diagramOrientation="Up" scaleDependency="Area" opacity="1" sizeScale="3x:0,0,0,0,0,0" lineSizeScale="3x:0,0,0,0,0,0" rotationOffset="270" width="15" scaleBasedVisibility="0" minScaleDenominator="0" lineSizeType="MM">
      <fontProperties style="" description="Ubuntu,11,-1,5,50,0,0,0,0,0"/>
      <attribute color="#000000" field="" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" zIndex="0" showAll="1" dist="0" obstacle="0" placement="0" linePlacementFlags="2">
    <properties>
      <Option type="Map">
        <Option type="QString" value="" name="name"/>
        <Option name="properties"/>
        <Option type="QString" value="collection" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions geometryPrecision="0" removeDuplicateNodes="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="id_add">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="AllowNull"/>
            <Option type="int" value="2147483647" name="Max"/>
            <Option type="int" value="-2147483648" name="Min"/>
            <Option type="int" value="0" name="Precision"/>
            <Option type="int" value="1" name="Step"/>
            <Option type="QString" value="SpinBox" name="Style"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="total_images">
      <editWidget type="Range">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="AllowNull"/>
            <Option type="int" value="2147483647" name="Max"/>
            <Option type="int" value="-2147483648" name="Min"/>
            <Option type="int" value="0" name="Precision"/>
            <Option type="int" value="1" name="Step"/>
            <Option type="QString" value="SpinBox" name="Style"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="images">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="true" name="IsMultiline"/>
            <Option type="bool" value="true" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="date_add">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option type="bool" value="true" name="allow_null"/>
            <Option type="bool" value="true" name="calendar_popup"/>
            <Option type="QString" value="yyyy-MM-dd HH:mm:ss" name="display_format"/>
            <Option type="QString" value="yyyy-MM-dd HH:mm:ss" name="field_format"/>
            <Option type="bool" value="false" name="field_iso_format"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="crs_map">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="extent_map">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option type="bool" value="false" name="IsMultiline"/>
            <Option type="bool" value="false" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias index="0" name="" field="id_add"/>
    <alias index="1" name="" field="total_images"/>
    <alias index="2" name="" field="images"/>
    <alias index="3" name="" field="date_add"/>
    <alias index="4" name="" field="crs_map"/>
    <alias index="5" name="" field="extent_map"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default applyOnUpdate="0" field="id_add" expression=""/>
    <default applyOnUpdate="0" field="total_images" expression=""/>
    <default applyOnUpdate="0" field="images" expression=""/>
    <default applyOnUpdate="0" field="date_add" expression=""/>
    <default applyOnUpdate="0" field="crs_map" expression=""/>
    <default applyOnUpdate="0" field="extent_map" expression=""/>
  </defaults>
  <constraints>
    <constraint constraints="1" unique_strength="0" notnull_strength="2" exp_strength="0" field="id_add"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="total_images"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="images"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="date_add"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="crs_map"/>
    <constraint constraints="0" unique_strength="0" notnull_strength="0" exp_strength="0" field="extent_map"/>
  </constraints>
  <constraintExpressions>
    <constraint field="id_add" exp="" desc=""/>
    <constraint field="total_images" exp="" desc=""/>
    <constraint field="images" exp="" desc=""/>
    <constraint field="date_add" exp="" desc=""/>
    <constraint field="crs_map" exp="" desc=""/>
    <constraint field="extent_map" exp="" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
    <actionsetting type="1" capture="0" notificationMessage="" name="Go extent" isEnabledOnlyWhenEditable="0" shortTitle="GoExtent" id="{d99513ab-0ae4-4d09-9ed4-51bd3c8536bc}" action="from qgis.core import (&#xa;  QgsProject, QgsRectangle,&#xa;  QgsCoordinateReferenceSystem, QgsCoordinateTransform&#xa;)&#xa;from qgis import utils as QgsUtils&#xa;&#xa;extent_map = '[%extent_map%]'&#xa;smin, smax = extent_map.split(',')&#xa;smax = smax.strip()&#xa;xMin, yMin = map( lambda v: float(v),  smin.split(' ') )&#xa;xMax, yMax = map( lambda v: float(v),  smax.split(' ') )&#xa;extent = QgsRectangle( xMin, yMin, xMax, yMax )&#xa;&#xa;mapCanvas = QgsUtils.iface.mapCanvas()&#xa;crs_canvas = mapCanvas.mapSettings().destinationCrs()&#xa;crs_map = '[%crs_map%]'&#xa;if not crs_canvas.authid() == crs_map:&#xa;    crs_map = QgsCoordinateReferenceSystem( crs_map )&#xa;    ct = QgsCoordinateTransform ( crs_map, crs_canvas )&#xa;    extent = ct.transform( extent )&#xa;&#xa;mapCanvas.setExtent( extent)&#xa;layer_id = '[% @layer_id %]'&#xa;layer = QgsProject.instance().mapLayer( layer_id )&#xa;layer.triggerRepaint()&#xa;" icon="">
      <actionScope id="Feature"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column type="field" width="-1" hidden="0" name="id_add"/>
      <column type="field" width="-1" hidden="0" name="total_images"/>
      <column type="field" width="-1" hidden="0" name="crs_map"/>
      <column type="field" width="-1" hidden="0" name="extent_map"/>
      <column type="actions" width="-1" hidden="1"/>
      <column type="field" width="-1" hidden="0" name="images"/>
      <column type="field" width="-1" hidden="0" name="date_add"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- codificação: utf-8 -*-
"""
Os formulários do QGIS podem ter uma função Python que é chamada quando
o formulário
 é aberto.

QGIS forms can have a Python function that is called when the form is
opened.

Use esta função para adicionar lógica extra aos seus formulários.

Entre com o nome da função no campo "Python Init function".
Un exemplo a seguir:
"""
a partir de PyQt4.QtGui importe QWidget

def my_form_open(diálogo, camada, feição):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field name="area_ha" editable="0"/>
    <field name="crs_map" editable="0"/>
    <field name="date_add" editable="0"/>
    <field name="datetime" editable="0"/>
    <field name="extent_map" editable="0"/>
    <field name="html_images" editable="0"/>
    <field name="id_add" editable="0"/>
    <field name="images" editable="0"/>
    <field name="json_images" editable="0"/>
    <field name="total_images" editable="0"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="area_ha"/>
    <field labelOnTop="0" name="crs_map"/>
    <field labelOnTop="0" name="date_add"/>
    <field labelOnTop="0" name="datetime"/>
    <field labelOnTop="0" name="extent_map"/>
    <field labelOnTop="0" name="html_images"/>
    <field labelOnTop="0" name="id_add"/>
    <field labelOnTop="0" name="images"/>
    <field labelOnTop="0" name="json_images"/>
    <field labelOnTop="0" name="total_images"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id_add</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>

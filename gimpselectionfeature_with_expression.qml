<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis readOnly="0" simplifyAlgorithm="0" simplifyDrawingHints="1" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" maxScale="0" simplifyDrawingTol="1" simplifyMaxScale="1" simplifyLocal="1" version="3.4.0-Madeira" labelsEnabled="0" minScale="1e+8">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" type="singleSymbol" enableorderby="0" symbollevels="0">
    <symbols>
      <symbol type="fill" alpha="1" clip_to_extent="1" name="0">
        <layer class="SimpleLine" locked="0" enabled="1" pass="0">
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
    <property key="dualview/previewExpressions">
      <value>id_add</value>
    </property>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Pie">
    <DiagramCategory maxScaleDenominator="1e+8" minimumSize="0" opacity="1" backgroundColor="#ffffff" scaleDependency="Area" minScaleDenominator="0" backgroundAlpha="255" diagramOrientation="Up" penAlpha="255" lineSizeType="MM" penWidth="0" barWidth="5" height="15" sizeType="MM" enabled="0" sizeScale="3x:0,0,0,0,0,0" width="15" penColor="#000000" scaleBasedVisibility="0" labelPlacementMethod="XHeight" lineSizeScale="3x:0,0,0,0,0,0" rotationOffset="270">
      <fontProperties style="" description="Ubuntu,11,-1,5,50,0,0,0,0,0"/>
      <attribute field="" label="" color="#000000"/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings linePlacementFlags="2" obstacle="0" priority="0" dist="0" placement="0" zIndex="0" showAll="1">
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
    <field name="area_ha">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="id_add" index="0" name=""/>
    <alias field="total_images" index="1" name=""/>
    <alias field="images" index="2" name=""/>
    <alias field="date_add" index="3" name=""/>
    <alias field="crs_map" index="4" name=""/>
    <alias field="extent_map" index="5" name=""/>
    <alias field="area_ha" index="6" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="id_add" expression="" applyOnUpdate="0"/>
    <default field="total_images" expression="" applyOnUpdate="0"/>
    <default field="images" expression="" applyOnUpdate="0"/>
    <default field="date_add" expression="" applyOnUpdate="0"/>
    <default field="crs_map" expression="" applyOnUpdate="0"/>
    <default field="extent_map" expression="" applyOnUpdate="0"/>
    <default field="area_ha" expression="" applyOnUpdate="0"/>
  </defaults>
  <constraints>
    <constraint unique_strength="0" constraints="1" field="id_add" notnull_strength="2" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" field="total_images" notnull_strength="0" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" field="images" notnull_strength="0" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" field="date_add" notnull_strength="0" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" field="crs_map" notnull_strength="0" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" field="extent_map" notnull_strength="0" exp_strength="0"/>
    <constraint unique_strength="0" constraints="0" field="area_ha" notnull_strength="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint field="id_add" desc="" exp=""/>
    <constraint field="total_images" desc="" exp=""/>
    <constraint field="images" desc="" exp=""/>
    <constraint field="date_add" desc="" exp=""/>
    <constraint field="crs_map" desc="" exp=""/>
    <constraint field="extent_map" desc="" exp=""/>
    <constraint field="area_ha" desc="" exp=""/>
  </constraintExpressions>
  <expressionfields>
    <field subType="0" precision="4" comment="" type="6" typeName="double" length="10" expression="area(  transform( $geometry ,  'EPSG:4326', 'EPSG:5641') ) / 10000" name="area_ha"/>
  </expressionfields>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
    <actionsetting isEnabledOnlyWhenEditable="0" id="{a540c4bb-2689-4db2-8052-2be6dda5f498}" capture="0" shortTitle="GoExtent" type="1" icon="" notificationMessage="" name="Go extent" action="from qgis.core import (&#xa;  QgsProject, QgsRectangle,&#xa;  QgsCoordinateReferenceSystem, QgsCoordinateTransform&#xa;)&#xa;from qgis import utils as QgsUtils&#xa;&#xa;extent_map = '[%extent_map%]'&#xa;smin, smax = extent_map.split(',')&#xa;smax = smax.strip()&#xa;xMin, yMin = map( lambda v: float(v),  smin.split(' ') )&#xa;xMax, yMax = map( lambda v: float(v),  smax.split(' ') )&#xa;extent = QgsRectangle( xMin, yMin, xMax, yMax )&#xa;&#xa;mapCanvas = QgsUtils.iface.mapCanvas()&#xa;crs_canvas = mapCanvas.mapSettings().destinationCrs()&#xa;crs_map = '[%crs_map%]'&#xa;if not crs_canvas.authid() == crs_map:&#xa;    crs_map = QgsCoordinateReferenceSystem( crs_map )&#xa;    ct = QgsCoordinateTransform ( crs_map, crs_canvas )&#xa;    extent = ct.transform( extent )&#xa;&#xa;mapCanvas.setExtent( extent)&#xa;layer_id = '[% @layer_id %]'&#xa;layer = QgsProject.instance().mapLayer( layer_id )&#xa;layer.triggerRepaint()&#xa;">
      <actionScope id="Feature"/>
    </actionsetting>
  </attributeactions>
  <attributetableconfig sortExpression="" sortOrder="0" actionWidgetStyle="dropDown">
    <columns>
      <column hidden="0" type="field" width="-1" name="id_add"/>
      <column hidden="0" type="field" width="-1" name="total_images"/>
      <column hidden="0" type="field" width="-1" name="crs_map"/>
      <column hidden="0" type="field" width="-1" name="extent_map"/>
      <column hidden="1" type="actions" width="-1"/>
      <column hidden="0" type="field" width="-1" name="images"/>
      <column hidden="0" type="field" width="-1" name="date_add"/>
      <column hidden="0" type="field" width="-1" name="area_ha"/>
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
    <field editable="0" name="area_ha"/>
    <field editable="0" name="crs_map"/>
    <field editable="0" name="date_add"/>
    <field editable="0" name="datetime"/>
    <field editable="0" name="extent_map"/>
    <field editable="0" name="html_images"/>
    <field editable="0" name="id_add"/>
    <field editable="0" name="images"/>
    <field editable="0" name="json_images"/>
    <field editable="0" name="total_images"/>
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

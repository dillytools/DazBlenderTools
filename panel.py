import bpy
from . import utils

#----------------------------------------------------------
#   Viewport Tab
#----------------------------------------------------------

class DAZTOOLS_PT_ToolsTab:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Daz Tools"
    bl_options = {'DEFAULT_CLOSED'}

#----------------------------------------------------------
#   Panels
#----------------------------------------------------------

class DAZTOOLS_PT_Data(DAZTOOLS_PT_ToolsTab, bpy.types.Panel):
    bl_label = "Data"
    bl_idname = "DAZTOOLS_PT_Data"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "primary_armature_enum", text="Armature")
        layout.prop(context.scene, "primary_mesh_enum", text="Mesh")
        layout.prop(context.scene, "female_anatomy_mesh_enum", text="Female Anatomy")
        layout.prop(context.scene, "male_anatomy_mesh_enum", text="Male Anatomy")
        layout.prop(context.scene, "paint_mesh_enum", text="Paint Mesh")

class DAZTOOLS_PT_ClothingTools(DAZTOOLS_PT_ToolsTab, bpy.types.Panel):
    bl_label = "Clothing"
    bl_idname = "DAZTOOLS_PT_ClothingTools"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        selected_names = [obj.name for obj in context.selected_objects]

        if not selected_names:
            layout.label(text="No objects selected.")
        else:
            for name in selected_names:
                layout.label(text=name)
                
        layout.separator()
        layout.operator("daztools.reparent_to_armature", text="Reparent to Armature")
        layout.operator("daztools.copy_weights", text="Copy Weights")
        layout.operator("daztools.export_clothing", text="Export")

class DAZTOOLS_PT_VertexWeightTools(DAZTOOLS_PT_ToolsTab, bpy.types.Panel):
    bl_label = "Vertex Weight Tools"
    bl_idname = "DAZTOOLS_PT_VertexWeightTools"
    bl_parent_id = "DAZTOOLS_PT_ClothingTools"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "vertex_smooth_factor", text="Smooth Factor")
        layout.prop(context.scene, "vertex_smooth_iterations", text="Smooth Iterations")
        layout.separator()
        layout.operator("daztools.apply_vertex_smoothing", text="Apply Smoothing To Vertex Group")

class DAZTOOLS_PT_MorphTools(DAZTOOLS_PT_ToolsTab, bpy.types.Panel):
    bl_label = "Morph Tools"
    bl_idname = "DAZTOOLS_PT_MorphTools"
    bl_parent_id = "DAZTOOLS_PT_ClothingTools"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.operator("daz.transfer_shapekeys", text="Transfer Shapekeys")
        layout.separator()
        row = layout.row()  
        row.operator("daztools.preview_morph", text="Preview Morph")
        row.operator("daztools.preview_next_morph", text="Preview Next")
        row.operator("daztools.preview_prev_morph", text="Preview Previous")
        layout.separator()
        layout.operator("daztools.clear_morphs", text="Clear Morphs")
        layout.operator("daztools.select_default_shapekey", text="Select Default Shapekey")
        layout.separator()
        layout.operator("daztools.add_tucked_base_morph", text="Add Tucked Base Morph")
        layout.operator("daztools.add_tucked_morphs", text="Add Tucked Morphs")
        layout.operator("daztools.next_tucked_morph", text="Next Tucked Morph")
   
class DAZTOOLS_PT_VertexColorTools(DAZTOOLS_PT_ToolsTab, bpy.types.Panel):
    bl_label = "Vertex Color Tools"
    bl_idname = "DAZTOOLS_PT_VertexColorTools"
    bl_parent_id = "DAZTOOLS_PT_ClothingTools"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.operator("daztools.copy_vertex_paint", text="Copy Vertex Paint")
        layout.operator("daztools.copy_male_gens_paint", text="Copy Male Gens Paint")
        layout.operator("daztools.merge_paint_groups", text="Merge Paint Groups")

class DAZTOOLS_PT_DebugTools(DAZTOOLS_PT_ToolsTab, bpy.types.Panel):
    bl_label = "Debug"
    bl_idname = "DAZTOOLS_PT_DebugTools"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.operator("daztools.print_vertex_weight", text="Print Vertex Weight")

#----------------------------------------------------------
#   Operators
#----------------------------------------------------------

class DAZTOOLS_OT_ReparentToArmature(bpy.types.Operator):
    bl_label = "Reparent to Armature"
    bl_idname = "daztools.reparent_to_armature"
    bl_parent_id = "DAZTOOLS_PT_ClothingTools"
    bl_description = "Clear current parents and reparent selected objects to chosen armature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_armature_name = context.scene.primary_armature_enum
        selected_armature = bpy.data.objects.get(selected_armature_name)
        clothing_objects = context.selected_objects

        if not selected_armature or selected_armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Valid armature not selected")
            return {'CANCELLED'}
        
        if not clothing_objects:
            self.report({'ERROR'}, "There were no selected objects")
            return {'CANCELLED'}

        prev_armature = None

        for obj in clothing_objects:
            for mod in obj.modifiers:
                if obj != selected_armature:
                    obj.parent = None  # Clear parent
                    obj.parent = selected_armature
                if mod.type == 'ARMATURE':
                    prev_armature = mod.object
                    mod.object = selected_armature
                if mod.type == 'SUBSURF':
                    obj.modifiers.remove(mod)

        if prev_armature is not None:
            utils.delete_hierarchy(prev_armature)

        self.report({'INFO'}, f"Reparented {len(clothing_objects)} objects to '{selected_armature_name}'")
        return {'FINISHED'}
    
class DAZTOOLS_OT_CopyWeights(bpy.types.Operator):
    bl_label = "Copy Weights"
    bl_idname = "daztools.copy_weights"
    bl_parent_id = "DAZTOOLS_PT_ClothingTools"
    bl_description = "Copy weights from chosen mesh to selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_mesh_name = context.scene.primary_mesh_enum
        selected_mesh = bpy.data.objects.get(selected_mesh_name)
        clothing_objects = context.selected_objects

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if not selected_mesh or selected_mesh.type != 'MESH':
            self.report({'ERROR'}, "Valid mesh not selected")
            return {'CANCELLED'}
        
        if not clothing_objects:
            self.report({'ERROR'}, "There were no selected objects")
            return {'CANCELLED'}
        
        for obj in clothing_objects:
            obj.vertex_groups.clear()
            mod = obj.modifiers.new(name="CopyWeights", type='DATA_TRANSFER')
            mod.object = selected_mesh
            mod.use_vert_data = True
            mod.data_types_verts = {'VGROUP_WEIGHTS'}
            mod.vert_mapping = 'POLYINTERP_NEAREST'

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.datalayout_transfer(modifier="CopyWeights")
            bpy.ops.object.modifier_apply(modifier=mod.name)
            
        utils.prune_vertex_groups(clothing_objects)

        self.report({'INFO'}, f"Copied weights from '{selected_mesh_name}' to {len(clothing_objects)} objects")
        return {'FINISHED'}
    
class DAZTOOLS_OT_ApplyVertexGroupSmoothing(bpy.types.Operator):
    bl_label = "Apply Vertex Weight Smoothing"
    bl_idname = "daztools.apply_vertex_smoothing"
    bl_parent_id = "DAZTOOLS_PT_VertexWeightTools"
    bl_description = "Apply smoothing to the active vertex group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object

        smooth_factor = bpy.context.scene.vertex_smooth_factor
        smooth_iterations = bpy.context.scene.vertex_smooth_iterations

        if obj and obj.type == 'MESH':
            vg = obj.vertex_groups.active
            if vg:
                bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        
        # Apply smoothing to the active vertex group
        bpy.ops.object.vertex_group_smooth(
            group_select_mode='ACTIVE',
            factor=smooth_factor,        # Strength of smoothing (0–1)
            repeat=smooth_iterations     # Number of iterations
        )

        return {'FINISHED'}
    
class DAZTOOLS_OT_PreviewMorph(bpy.types.Operator):
    bl_label = "Preview Morph"
    bl_idname = "daztools.preview_morph"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Preview the current morph target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        selected_mesh_name = context.scene.primary_mesh_enum
        selected_mesh = bpy.data.objects.get(selected_mesh_name)

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if obj and obj.data.shape_keys:
            active_key = obj.active_shape_key  

        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")
        obj.use_mesh_mirror_x = True

        active_key.value = 1.0
        mesh_key = selected_mesh.data.shape_keys.key_blocks.get(active_key.name)
        mesh_key.value = 1.0

        selected_mesh.active_shape_key_index = utils.get_shapekey_index(selected_mesh, mesh_key)

        return {'FINISHED'}
    
class DAZTOOLS_OT_PreviewNextMorph(bpy.types.Operator):
    bl_label = "Preview Next Morph"
    bl_idname = "daztools.preview_next_morph"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Preview the next morph target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        selected_mesh_name = context.scene.primary_mesh_enum
        selected_mesh = bpy.data.objects.get(selected_mesh_name)

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if obj and obj.data.shape_keys:
            active_key = obj.active_shape_key
            active_key_index = obj.active_shape_key_index
            prev_key = obj.data.shape_keys.key_blocks[active_key_index - 1]

        utils.clear_shapekeys(obj)
        utils.clear_shapekeys(selected_mesh)

        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")
        obj.use_mesh_mirror_x = True

        prev_key.value = 1.0
        mesh_key = selected_mesh.data.shape_keys.key_blocks.get(prev_key.name)
        mesh_key.value = 1.0

        obj.active_shape_key_index = utils.get_shapekey_index(obj, prev_key)
        selected_mesh.active_shape_key_index = utils.get_shapekey_index(selected_mesh, mesh_key)
        
        return {'FINISHED'}
    
class DAZTOOLS_OT_PreviewPreviousMorph(bpy.types.Operator):
    bl_label = "Preview Previous Morph"
    bl_idname = "daztools.preview_prev_morph"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Preview the previous morph target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        selected_mesh_name = context.scene.primary_mesh_enum
        selected_mesh = bpy.data.objects.get(selected_mesh_name)

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if obj and obj.data.shape_keys:
            active_key = obj.active_shape_key
            active_key_index = obj.active_shape_key_index
            if (active_key_index + 1 < len(obj.data.shape_keys.key_blocks)):
                next_key = obj.data.shape_keys.key_blocks[active_key_index + 1]
            else:
                self.report({'ERROR'}, "No previous morph")
                return {'CANCELLED'}

        utils.clear_shapekeys(obj)
        utils.clear_shapekeys(selected_mesh)

        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Smooth")
        obj.use_mesh_mirror_x = True

        next_key.value = 1.0
        mesh_key = selected_mesh.data.shape_keys.key_blocks.get(next_key.name)
        mesh_key.value = 1.0

        obj.active_shape_key_index = utils.get_shapekey_index(obj, next_key)
        selected_mesh.active_shape_key_index = utils.get_shapekey_index(selected_mesh, mesh_key)
        
        return {'FINISHED'}

class DAZTOOLS_OT_ClearMorphs(bpy.types.Operator):
    bl_label = "Clear Morphs"
    bl_idname = "daztools.clear_morphs"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Clear all morphs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        selected_mesh_name = context.scene.primary_mesh_enum
        selected_mesh = bpy.data.objects.get(selected_mesh_name)
        female_mesh_name = context.scene.female_anatomy_mesh_enum
        female_mesh = bpy.data.objects.get(female_mesh_name)
        male_mesh_name = context.scene.male_anatomy_mesh_enum
        male_mesh = bpy.data.objects.get(male_mesh_name)

        utils.clear_shapekeys(obj)
        utils.clear_shapekeys(selected_mesh)
        utils.clear_shapekeys(female_mesh)
        utils.clear_shapekeys(male_mesh)

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        obj.active_shape_key_index = 0
        selected_mesh.active_shape_key_index = 0
        female_mesh.active_shape_key = 0
        male_mesh.active_shape_key = 0

        return {'FINISHED'}

class DAZTOOLS_OT_SelectDefaultShapekey(bpy.types.Operator):
    bl_label = "Select Default Shapekey"
    bl_idname = "daztools.select_default_shapekey"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Select Default Shapekey"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        selected_mesh_name = context.scene.primary_mesh_enum
        selected_mesh = bpy.data.objects.get(selected_mesh_name)

        obj.active_shape_key_index = 0
        selected_mesh.active_shape_key_index = 0

        return {'FINISHED'}

class DAZTOOLS_OT_CopyVertexPaint(bpy.types.Operator):
    bl_label = "Copy Vertex Paint"
    bl_idname = "daztools.copy_vertex_paint"
    bl_parent_id = "DAZTOOLS_PT_VertexPaintTools"
    bl_description = "Copy vertex paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        paint_mesh_name = context.scene.paint_mesh_enum
        paint_mesh = bpy.data.objects.get(paint_mesh_name)

        obj.active_shape_key_index = 0
        paint_mesh.active_shape_key_index = 0

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if not paint_mesh or obj.type != 'MESH':
            self.report({'ERROR'}, "Paint mesh not found")
            return {'CANCELLED'}
        
        if not obj:
            self.report({'ERROR'}, "There was no selected object")
            return {'CANCELLED'}
        
        mod = obj.modifiers.new(name="CopyVertexColors", type='DATA_TRANSFER')
        mod.object = paint_mesh
        mod.use_vert_data = True
        mod.data_types_verts = {'COLOR_VERTEX'}
        mod.vert_mapping = 'POLYINTERP_NEAREST'

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.datalayout_transfer(modifier="CopyVertexColors")
        bpy.ops.object.modifier_apply(modifier=mod.name)

        if bpy.context.mode != 'VERTEX_PAINT':
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Blur")
            obj.use_mesh_mirror_x = True
            obj.data.color_attributes.active_color = obj.data.color_attributes.get("Attribute")


        self.report({'INFO'}, f"Copied vertex colors from '{paint_mesh.name}' to selected object")
        return {'FINISHED'}

class DAZTOOLS_OT_CopyMaleGensPaint(bpy.types.Operator):
    bl_label = "Copy Male Gens Paint"
    bl_idname = "daztools.copy_male_gens_paint"
    bl_parent_id = "DAZTOOLS_PT_VertexPaintTools"
    bl_description = "Copy male gens paint"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        paint_mesh_name = context.scene.male_anatomy_mesh_enum
        paint_mesh = bpy.data.objects.get(paint_mesh_name)

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if not paint_mesh or obj.type != 'MESH':
            self.report({'ERROR'}, "Paint mesh not found")
            return {'CANCELLED'}
        
        if not obj:
            self.report({'ERROR'}, "There was no selected object")
            return {'CANCELLED'}
        
        utils.set_active_shapekey_by_name(obj, "TuckedBase")
        utils.set_active_shapekey_by_name(paint_mesh, "TuckedBase")

        obj.active_shape_key.value = 1.0
        paint_mesh.active_shape_key.value = 1.0
        
        mod = obj.modifiers.new(name="CopyVertexColors", type='DATA_TRANSFER')
        mod.object = paint_mesh
        mod.use_vert_data = True
        mod.data_types_verts = {'COLOR_VERTEX'}
        mod.vert_mapping = 'POLYINTERP_NEAREST'

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.datalayout_transfer(modifier="CopyVertexColors")
        bpy.ops.object.modifier_apply(modifier=mod.name)

        if bpy.context.mode != 'VERTEX_PAINT':
            bpy.ops.object.mode_set(mode='VERTEX_PAINT')
            bpy.ops.wm.tool_set_by_id(name="builtin_brush.Blur")
            obj.use_mesh_mirror_x = True
            obj.data.color_attributes.active_color = obj.data.color_attributes.get("Penis")

        self.report({'INFO'}, f"Copied vertex colors from '{paint_mesh.name}' to selected object")
        return {'FINISHED'}

class DAZTOOLS_OT_MergePaintGroups(bpy.types.Operator):
    bl_label = "Merge Paint Groups"
    bl_idname = "daztools.merge_paint_groups"
    bl_parent_id = "DAZTOOLS_PT_VertexPaintTools"
    bl_description = "Merge paint groups"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        paint_mesh_name = context.scene.male_anatomy_mesh_enum
        paint_mesh = bpy.data.objects.get(paint_mesh_name)
        mesh = obj.data

        src_attribute = mesh.color_attributes.get("Attribute")
        dst_attribute = mesh.color_attributes.get("Penis")
        dst_channel_idx = 1
        src_channel_idx = 1

        for i, src_av in enumerate(src_attribute.data):
                dst_attribute.data[i].color[dst_channel_idx] = src_av.color[src_channel_idx]

        mesh.color_attributes.remove(src_attribute)
        mesh.color_attributes.active.name = "Attribute"

        utils.clear_shapekeys(obj)
        utils.clear_shapekeys(paint_mesh)

        self.report({'INFO'}, f"Merged vertex colors on selected object")
        return {'FINISHED'}

class DAZTOOLS_OT_ExportClothing(bpy.types.Operator):
    bl_label = "Export Clothing"
    bl_idname = "daztools.export_clothing"
    bl_parent_id = "DAZTOOLS_PT_VertexPaintTools"
    bl_description = "Export clothing"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        armature_name = context.scene.primary_armature_enum
        armature = bpy.data.objects.get(armature_name)

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        if not obj or not armature:
            self.report({'ERROR'}, "Missing object or armature")
            return {'CANCELLED'}
        
        obj.active_shape_key_index = 0

        # trick to ensure mesh doesn't export with applied shape key
        if bpy.context.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        armature.select_set(True)

        # Unlock scale for object and armature
        for target in (obj, armature):
            target.lock_scale[0] = False
            target.lock_scale[1] = False
            target.lock_scale[2] = False

        # Scale both by 100
        armature.scale *= 100.0

        # Apply scale
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        bpy.ops.export_scene.fbx(
            'INVOKE_DEFAULT',
            filepath = "D:/UE Projects/Characters/Base Female/Clothing/",
            use_selection = True,
            use_visible = True,
            use_active_collection = False,
            global_scale = 0.009999999776482582,
            apply_unit_scale = True,
            apply_scale_options = 'FBX_SCALE_NONE',
            use_space_transform = True,
            bake_space_transform = False,
            object_types = {'ARMATURE', 'MESH'},
            use_mesh_modifiers = False,
            use_mesh_modifiers_render = True,
            mesh_smooth_type = 'FACE',
            colors_type = 'SRGB',
            prioritize_active_color = False,
            use_subsurf = False,
            use_mesh_edges = False,
            use_tspace = False,
            use_triangles = False,
            use_custom_props = False,
            add_leaf_bones = False,
            primary_bone_axis = 'Y',
            secondary_bone_axis = 'X',
            use_armature_deform_only = False,
            armature_nodetype = 'NULL',
            bake_anim = False,
            bake_anim_use_all_bones = True,
            bake_anim_use_nla_strips = True,
            bake_anim_use_all_actions = True,
            bake_anim_force_startend_keying = True,
            bake_anim_step = 1.0,
            bake_anim_simplify_factor = 1.0,
            path_mode = 'AUTO',
            embed_textures = False,
            batch_mode = 'OFF',
            use_batch_own_dir = True,
            axis_forward = '-Z',
            axis_up = 'Y',
        )

        self.report({'INFO'}, f"Successfully exported clothing")
        return {'FINISHED'}

class DAZTOOLS_OT_AddTuckedBaseMorph(bpy.types.Operator):
    bl_label = "Add Tucked Base Morph"
    bl_idname = "daztools.add_tucked_base_morph"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Add Tucked Base Morph"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        male_anatomy_mesh_name = context.scene.male_anatomy_mesh_enum
        male_anatomy_mesh = bpy.data.objects.get(male_anatomy_mesh_name)

        shape_name = "TuckedBase"

        if not obj or not male_anatomy_mesh:
            self.report({'ERROR'}, "Valid object not selected")
            return {'CANCELLED'}
        
        if shape_name in obj.data.shape_keys.key_blocks:
            self.report({'ERROR'}, "Object already has tucked base morph")
            return {'CANCELLED'}

        obj.shape_key_add(name="TuckedBase", from_mix=False)

        new_key = obj.data.shape_keys.key_blocks.get(shape_name)
        obj.active_shape_key_index = utils.get_shapekey_index(obj, new_key)
        new_key.value = 1.0

        # Make sure it's not hidden in the current view layer
        male_anatomy_mesh.hide_set(False)

        mesh_key = male_anatomy_mesh.data.shape_keys.key_blocks.get(shape_name)
        mesh_key.value = 1.0

        bpy.ops.object.mode_set(mode='SCULPT')
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Grab")
        obj.use_mesh_mirror_x = True

        self.report({'INFO'}, f"Added tucked base morph to object")
        return {'FINISHED'}

class DAZTOOLS_OT_AddTuckedMorphs(bpy.types.Operator):
    bl_label = "Add Tucked Morphs"
    bl_idname = "daztools.add_tucked_morphs"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Add Tucked Morphs"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        male_anatomy_mesh_name = context.scene.male_anatomy_mesh_enum
        male_anatomy_mesh = bpy.data.objects.get(male_anatomy_mesh_name)

        shape_names = ["TuckedMax", "TuckedShaftMax", "TuckedScrotumMax"]

        if any(name in shape_names for name in obj.data.shape_keys.key_blocks):
            self.report({'ERROR'}, "Object already has tucked morphs")
            return {'CANCELLED'}

        for name in shape_names:
            obj.shape_key_add(name=name, from_mix=True)

        utils.clear_shapekeys(obj)
        utils.clear_shapekeys(male_anatomy_mesh)

        male_key = male_anatomy_mesh.data.shape_keys.key_blocks.get("TuckedMax")
        male_anatomy_mesh.active_shape_key_index = utils.get_shapekey_index(male_anatomy_mesh, male_key)
        male_key.value = 1.0

        obj_key = obj.data.shape_keys.key_blocks.get("TuckedMax")
        obj.active_shape_key_index = utils.get_shapekey_index(obj, obj_key)
        obj_key.value = 1.0

        self.report({'INFO'}, f"Added tucked morphs to object")
        return {'FINISHED'}

class DAZTOOLS_OT_NextTuckedMorph(bpy.types.Operator):
    bl_label = "Next Tucked Morph"
    bl_idname = "daztools.next_tucked_morph"
    bl_parent_id = "DAZTOOLS_PT_MorphTools"
    bl_description = "Next Tucked Morph"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        male_anatomy_mesh_name = context.scene.male_anatomy_mesh_enum
        male_anatomy_mesh = bpy.data.objects.get(male_anatomy_mesh_name)

        if obj and obj.data.shape_keys:
            active_key = obj.active_shape_key  
        else:
            self.report({'ERROR'}, "No object with shape keys selected")
            return {'CANCELLED'}

        active_key = obj.data.shape_keys.key_blocks.get(active_key.name)

        if active_key.name == "TuckedMax":
            next_key_name = "TuckedShaftMax"
        elif active_key.name == "TuckedShaftMax":
            next_key_name = "TuckedScrotumMax"
        elif active_key.name == "TuckedScrotumMax":
            self.report({'ERROR'}, "No more tucked morphs")
            return {'CANCELLED'}
        else:
            self.report({'ERROR'}, "No tucked morph selected")
            return {'CANCELLED'}
        
        utils.clear_shapekeys(obj)
        utils.clear_shapekeys(male_anatomy_mesh)

        male_key = male_anatomy_mesh.data.shape_keys.key_blocks.get(next_key_name)
        male_anatomy_mesh.active_shape_key_index = utils.get_shapekey_index(male_anatomy_mesh, male_key)
        male_key.value = 1.0

        obj_key = obj.data.shape_keys.key_blocks.get(next_key_name)
        obj.active_shape_key_index = utils.get_shapekey_index(obj, obj_key)
        obj_key.value = 1.0

        self.report({'INFO'}, f"Moved to next tucked morph")
        return {'FINISHED'}

class DAZTOOLS_OT_GlobalSettings(bpy.types.Operator):
    bl_idname = "daztools.global_settings"
    bl_label = "Global Settings"
    bl_description = "Show or update global settings"
    bl_options = {'UNDO', 'PRESET'}

#-------------------------------------------------------------
#   Debug
#-------------------------------------------------------------

class DAZTOOLS_OT_PrintVertexWeight(bpy.types.Operator):
    bl_label = "Print Vertex Weight"
    bl_idname = "daztools.print_vertex_weight"
    bl_parent_id = "DAZTOOLS_PT_DebugTools"
    bl_description = "Print weight value of selected vertex group"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object

        active_vgroup = None

        if obj and obj.type == 'MESH':
            active_vgroup = obj.vertex_groups.active
            
        if not active_vgroup or not obj or not obj.type == 'MESH':
            self.report({'INFO'}, f"No vertex group selected")

        max_weight = 0.0

        if active_vgroup:
            for v in obj.data.vertices:
                for g in v.groups:
                    if g.group == active_vgroup.index:
                        max_weight = max(max_weight, g.weight)

        self.report({'INFO'}, f"Vertex group '{active_vgroup.name}' has value '{max_weight}")
        return {'FINISHED'}

#-------------------------------------------------------------
#   Initialize
#-------------------------------------------------------------

classes = [
    DAZTOOLS_PT_Data,
    DAZTOOLS_PT_ClothingTools,
    DAZTOOLS_PT_DebugTools,
    DAZTOOLS_PT_VertexWeightTools,
    DAZTOOLS_PT_MorphTools,
    DAZTOOLS_PT_VertexColorTools,
    DAZTOOLS_OT_ReparentToArmature,
    DAZTOOLS_OT_CopyWeights,
    DAZTOOLS_OT_PrintVertexWeight,
    DAZTOOLS_OT_ApplyVertexGroupSmoothing,
    DAZTOOLS_OT_PreviewMorph,
    DAZTOOLS_OT_PreviewNextMorph,
    DAZTOOLS_OT_PreviewPreviousMorph,
    DAZTOOLS_OT_ClearMorphs,
    DAZTOOLS_OT_SelectDefaultShapekey,
    DAZTOOLS_OT_CopyVertexPaint,
    DAZTOOLS_OT_AddTuckedBaseMorph,
    DAZTOOLS_OT_AddTuckedMorphs,
    DAZTOOLS_OT_NextTuckedMorph,
    DAZTOOLS_OT_CopyMaleGensPaint,
    DAZTOOLS_OT_MergePaintGroups,
    DAZTOOLS_OT_ExportClothing
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
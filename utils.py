import bpy

#-------------------------------------------------------------
#   Armature Operations
#-------------------------------------------------------------

def get_armature_items(self, context):
    items = []
    for obj in context.scene.objects:
        if obj.type == 'ARMATURE':
            items.append((obj.name, obj.name, "Armature object"))
    return items if items else [("NONE", "No Armatures", "")]

def get_mesh_items(self, context):
    items = []
    for obj in context.scene.objects:
        if obj.type == 'MESH':
            items.append((obj.name, obj.name, "Mesh object"))
    return items if items else [("NONE", "No Meshes", "")]

def delete_hierarchy(obj):
    # Gather all children recursively
    to_delete = []

    def collect(obj):
        to_delete.append(obj)
        for child in obj.children:
            collect(child)

    collect(obj)

    # Deselect everything
    bpy.ops.object.select_all(action='DESELECT')

    # Select the hierarchy for deletion
    for ob in to_delete:
        ob.select_set(True)

    # Set an active object (needed for delete operator)
    bpy.context.view_layer.objects.active = obj

    # Delete selected objects
    bpy.ops.object.delete()

#-------------------------------------------------------------
#   Prune vertex groups
#-------------------------------------------------------------

def survey(obj):
            maxWeight = {}
            for i in obj.vertex_groups:
                maxWeight[i.index] = 0

            for v in obj.data.vertices:
                for g in v.groups:
                    gn = g.group 
                    w = obj.vertex_groups[g.group].weight(v.index)
                    if (maxWeight.get(gn) is None or w>maxWeight[gn]):
                        maxWeight[gn] = w
            return maxWeight

def prune_vertex_groups(objects):
    for obj in objects:
            maxWeight = survey(obj)
            ka = []
            ka.extend(maxWeight.keys())
            ka.sort(key=lambda gn: -gn) # Inverse it, so remove can works well.
            for gn in ka:
                if maxWeight[gn]<=0.000001:
                    obj.vertex_groups.remove(obj.vertex_groups[gn]) # actually remove the group

# --------------------------------------
#   Morph Operations
# --------------------------------------

def get_shapekey_index(obj, shapekey):
    if obj and obj.data.shape_keys:
        for i, key in enumerate(obj.data.shape_keys.key_blocks):
            if key.name == shapekey.name:
                return i
    return -1  # Not found

def clear_shapekeys(obj):
    # Ignored keys
    keep_keys = {"HideNips"}

    if obj and obj.data.shape_keys:
            for key_block in obj.data.shape_keys.key_blocks:
                if key_block.name not in keep_keys:
                    key_block.value = 0.0

def set_active_shapekey_by_name(obj, shapekey_name):
    if obj and obj.data.shape_keys:
        for i, key in enumerate(obj.data.shape_keys.key_blocks):
            if key.name == shapekey_name:
                obj.active_shape_key_index = i

# --------------------------------------
#   Register/Unregister Float Property
# --------------------------------------

def register_float_property(name, default=1.0, min_val=0.0, max_val=100.0):
    setattr(
        bpy.types.Scene,
        name,
        bpy.props.FloatProperty(
            name=name.replace("_", " ").title(),
            description=f"{name} value",
            default=default,
            min=min_val,
            max=max_val
        )
    )

def unregister_float_property(name):
    if hasattr(bpy.types.Scene, name):
        delattr(bpy.types.Scene, name)

# --------------------------------------
#   Register/Unregister Int Property
# --------------------------------------

def register_int_property(name, default=1, min_val=0, max_val=1):
    setattr(
        bpy.types.Scene,
        name,
        bpy.props.IntProperty(
            name=name.replace("_", " ").title(),
            description=f"{name} value",
            default=default,
            min=min_val,
            max=max_val
        )
    )

def unregister_int_property(name):
    if hasattr(bpy.types.Scene, name):
        delattr(bpy.types.Scene, name)

# --------------------------------------
#   Register/Unregister Enum Property
# --------------------------------------

def register_props():
    bpy.types.Scene.primary_armature_enum = bpy.props.EnumProperty(
        name="Armature",
        description="Select an armature",
        items=get_armature_items
    )
    bpy.types.Scene.primary_mesh_enum = bpy.props.EnumProperty(
        name="Mesh",
        description="Select a mesh",
        items=get_mesh_items
    )
    bpy.types.Scene.female_anatomy_mesh_enum = bpy.props.EnumProperty(
        name="Female Anatomy Mesh",
        description="Select a mesh",
        items=get_mesh_items
    )
    bpy.types.Scene.male_anatomy_mesh_enum = bpy.props.EnumProperty(
        name="Male Anatomy Mesh",
        description="Select a mesh",
        items=get_mesh_items
    )
    bpy.types.Scene.paint_mesh_enum = bpy.props.EnumProperty(
        name="Paint Mesh",
        description="Select a mesh",
        items=get_mesh_items
    )

def unregister_props():
    del bpy.types.Scene.primary_armature_enum
    del bpy.types.Scene.primary_mesh_enum
    del bpy.types.Scene.female_anatomy_mesh_enum
    del bpy.types.Scene.male_anatomy_mesh_enum
    del bpy.types.Scene.paint_mesh_enum

# --------------------------------------
#   Blender registration hooks
# --------------------------------------

def register():
    register_props()
    register_float_property("vertex_smooth_factor", default=0.5, min_val=0.0, max_val=1.0)
    register_int_property("vertex_smooth_iterations", default=5, min_val=1, max_val=10)

def unregister():
    unregister_props()
    unregister_float_property("vertex_smooth_factor")
    unregister_int_property("vertex_smooth_iterations")
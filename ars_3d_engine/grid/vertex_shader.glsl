// Inputs from the VertexBuffer
attribute vec3 a_position;

// Varying variable to pass world position to fragment shader
varying vec3 v_world_pos;

void main() {
    v_world_pos = a_position;
    // $transform is a special variable that holds the complete
    // model-view-projection matrix from VisPy
    gl_Position = $transform(vec4(a_position, 1.0));
}
// Value received from the vertex shader, interpolated for each fragment
varying vec3 v_world_pos;

// Uniforms are global variables set by the Python code
uniform float u_minor_step;
uniform float u_major_step;
uniform float u_visible_distance;
uniform float u_fade_exponent;
uniform vec2 u_cam_xz_pos;

uniform vec4 u_minor_color;
uniform vec4 u_major_color;
uniform vec4 u_axis_x_color;
uniform vec4 u_axis_z_color;

uniform bool u_show_grid;
uniform bool u_show_x_axis;
uniform bool u_show_z_axis;

// Function to compute line intensity with anti-aliasing in screen space
float get_line_intensity(float dist, float pixel_width, float fw) {
    float half_width = pixel_width * fw * 0.5;
    float aa = fw * 0.5;
    float low = max(0.0, half_width - aa);
    float high = half_width + aa;
    return 1.0 - smoothstep(low, high, dist);
}

void main() {
    // --- Culling and Fading ---
    // Calculate distance from camera on the XZ plane
    float dist_from_cam = distance(v_world_pos.xz, u_cam_xz_pos);

    // Discard fragments far outside the visible radius for efficiency
    if (dist_from_cam > u_visible_distance + 2.0 * u_major_step) {
        discard;
    }

    // Calculate alpha for the fade-out effect
    float fade_alpha = clamp(1.0 - pow(dist_from_cam / u_visible_distance, u_fade_exponent), 0.0, 1.0);
    float axis_fade_alpha = clamp(0.8 - pow(dist_from_cam / u_visible_distance, u_fade_exponent), 0.0, 1.0);

    vec4 final_color = vec4(0.0, 0.0, 0.0, 0.0);

    // Compute fwidth for x and z directions
    vec2 fw = fwidth(v_world_pos.xz);

    // --- Grid Lines ---
    if (u_show_grid) {
        vec2 minor_dist = abs(mod(v_world_pos.xz + u_minor_step / 2.0, u_minor_step) - u_minor_step / 2.0);
        vec2 major_dist = abs(mod(v_world_pos.xz + u_major_step / 2.0, u_major_step) - u_major_step / 2.0);

        // Minor intensity (1.6 pixel width)
        float minor_x = get_line_intensity(minor_dist.x, 1.6, fw.x);
        float minor_y = get_line_intensity(minor_dist.y, 1.6, fw.y);
        float minor_intensity = max(minor_x, minor_y);

        // Major intensity (2 pixel width)
        float major_x = get_line_intensity(major_dist.x, 2.0, fw.x);
        float major_y = get_line_intensity(major_dist.y, 2.0, fw.y);
        float major_intensity = max(major_x, major_y);

        // Combined grid intensity
        float grid_intensity = max(minor_intensity, major_intensity);

        if (grid_intensity > 0.01) {
            // Mix factor for color
            float mix_factor = major_intensity / grid_intensity;
            vec4 grid_color = mix(u_minor_color, u_major_color, mix_factor);
            grid_color.a *= fade_alpha * grid_intensity;
            final_color = mix(final_color, grid_color, grid_intensity);
        }
    }
    
    // --- Axis Lines (2.0 pixel width) ---
    float pixel_axis_width = 2.0;
    if (u_show_x_axis) {
        float dist = abs(v_world_pos.z);
        float fw_dir = fw.y;  // Perpendicular to x-axis is z direction
        float x_axis_intensity = get_line_intensity(dist, pixel_axis_width, fw_dir);
        vec4 x_color = u_axis_x_color;
        x_color.a *= axis_fade_alpha;
        final_color = mix(final_color, x_color, x_axis_intensity);
    }
    if (u_show_z_axis) {
        float dist = abs(v_world_pos.x);
        float fw_dir = fw.x;  // Perpendicular to z-axis is x direction
        float z_axis_intensity = get_line_intensity(dist, pixel_axis_width, fw_dir);
        vec4 z_color = u_axis_z_color;
        z_color.a *= axis_fade_alpha;
        final_color = mix(final_color, z_color, z_axis_intensity);
    }

    // Discard fragments that are fully transparent
    if (final_color.a < 0.01) {
        discard;
    }

    gl_FragColor = final_color;
}
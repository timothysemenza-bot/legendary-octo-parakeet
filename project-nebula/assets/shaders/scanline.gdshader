shader_type canvas_item;

uniform float line_strength : hint_range(0.0, 1.0) = 0.12;
uniform float line_density : hint_range(80.0, 600.0) = 260.0;
uniform vec4 tint : source_color = vec4(0.7, 1.0, 0.85, 1.0);
uniform sampler2D screen_tex : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
	float scan = sin(UV.y * line_density) * 0.5 + 0.5;
	float shade = mix(1.0, 1.0 - line_strength, scan);
	vec4 base = texture(screen_tex, SCREEN_UV);
	COLOR = vec4(base.rgb * tint.rgb * shade, 0.35);
}

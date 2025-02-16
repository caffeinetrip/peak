#version 330 core

uniform sampler2D tex;
uniform float time;

in vec2 uvs;
out vec4 f_color;

float rand(vec2 n) { 
    return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
}

float noise(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {

    

    if (texture(tex, uvs).r == 0 && texture(tex, uvs).g == 0 && texture(tex, uvs).b == 0) {
        discard;
    }
    
    vec2 uv = uvs;
    
    vec2 offset = vec2(0.001, 0.001);
    vec4 color = texture(tex, uv);

    color.r = texture(tex, uv + offset * vec2(-1.0, 0.5) * (1.0 + sin(time))*0.8).r;
    color.g = texture(tex, uv + offset * vec2(0.0, -0.5) * (1.0 + cos(time))*0.8).g;
    color.b = texture(tex, uv + offset * vec2(1.0, 0.5) * (1.0 + sin(time))*0.8).b;

    float scanline = sin(uv.y * 1000.0 + time * 10.0) * 0.01;
    color.rgb += scanline;

    color.rgb *= 0.9 + 0.1 * rand(uv + time);

    vec2 vig = uv - 0.5;
    color.rgb *= 1.0 - dot(vig, vig) * 1.01;

    color.rgb += (noise(uv * 50.0 + time) - 0.5) * 0.05;

    color.rgb = mix(vec3(dot(color.rgb, vec3(0.299, 0.587, 0.114))), color.rgb, 0.6);
    color.rgb = mix(vec3(dot(color.rgb, vec3(0, 0, 0))), color.rgb, 0.99);

    f_color = color;
}

#version 330 core

uniform sampler2D tex;
uniform float time;
uniform vec2 resolution;
uniform float noise_cof;

uniform float timeScale = 0.25;
uniform float treshold = 0.3;
uniform float angleConst = 1.5;
uniform float stripeWidth = 60;
uniform float stripeImpact = 0.03;

in vec2 uvs;
out vec4 f_color;

float rand(vec2 n) { 
    return fract(sin(dot(n, vec2(12.9898, 4.1414))) * 43758.5453);
}

float noise(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

vec4 gradientBackground(vec2 uv) {
    vec4 color1 = vec4(0.15, 0.001, 0.001, 1.0); 
    vec4 color2 = vec4(0.15, 0.001, 0.001, 1.0);
    return mix(color1, color2, 0.0);
}

vec4 radialGlow(vec2 uv) {
    float dist = distance(uv, vec2(0.5, 0.5));
    float glow = smoothstep(0.7, 0.0, dist);
    return vec4(glow * 0.2);
}

void main() {
    vec2 uv = uvs;

    vec4 bgColor = gradientBackground(uv);

    bgColor += radialGlow(uv);

    float noiseValue = noise(uv * 10.0 + time * 0.1);
    bgColor += noiseValue * 0.05;

    bgColor += vec4(sin(time * 0.15) * 0.05, cos(time * 0.013) * 0.05, sin(time * 0.07) * 0.05, 1.0);

    vec4 color = vec4(bgColor);
    color.rgb = mix(vec3(dot(color.rgb, vec3(0, 0, 0))), color.rgb, 0.75);

    if (texture(tex, uv).r != 0 && texture(tex, uv).g != 0 && texture(tex, uv).b != 0) {
        color = texture(tex, uv);
    }

    float scanline = sin(uv.y * 1000.0 + time * 10.0) * 0.05;
    color.rgb += scanline;

    color.rgb *= 0.9 + 0.1 * rand(uv + time);

    vec2 vig = uv - 0.5;
    color.rgb *= 1.0 - dot(vig, vig) * 1.5  * noise_cof;

    color.rgb += (noise(uv * 50.0 + time) - 0.5) * 0.1 * noise_cof; 

    color.rgb = mix(vec3(dot(color.rgb, vec3(0.299, 0.587, 0.114))), color.rgb, 0.8);
    color.rgb = mix(vec3(dot(color.rgb, vec3(0, 0, 0))), color.rgb, 0.75);

    f_color = color;
}
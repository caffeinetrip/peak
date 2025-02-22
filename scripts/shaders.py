from array import array
import moderngl

BASE_PATH = 'shaders/'
class Shader:
    def __init__(self, vert_path, frag_paths):
        self.vert = open(BASE_PATH + vert_path + '.vert', 'r').read()
        self.frag_shaders = [open(BASE_PATH + frag_path + '.frag', 'r').read() for frag_path in frag_paths]
        
        self.ctx = moderngl.create_context()

        self.quad_buffer = self.ctx.buffer(data=array('f', [
            -1.0, 1.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
            1.0, -1.0, 1.0, 1.0,
        ]))

        self.programs = [
            self.ctx.program(vertex_shader=self.vert, fragment_shader=frag)
            for frag in self.frag_shaders
        ]
        
        self.render_objects = [
            self.ctx.vertex_array(program, [(self.quad_buffer, '2f 2f', 'vert', 'texcoord')])
            for program in self.programs
        ]
        
        self.current_shader = 0
    
    def surf_to_texture(self, surf):
        tex = self.ctx.texture(surf.get_size(), 4)
        tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        tex.swizzle = 'BGRA'
        tex.write(surf.get_view('1'))
        return tex

    def set_shader(self, index=0):
        if 0 <= index < len(self.programs):
            self.current_shader = index
        else:
            raise ValueError("Invalid shader index")

    def render(self, t, surf=None, ui_surf=None, noise_cof=1):
        
        if surf:
            frame_tex = self.surf_to_texture(surf)
            frame_tex.use(1)

            program = self.programs[0]
            
            program['tex'].value = 1
            program['time'].value = t
            program['noise_cof'].value = noise_cof
            
            self.render_objects[0].render(mode=moderngl.TRIANGLE_STRIP)
            
            frame_tex.release()
        
        if ui_surf:
        
            ui_tex = self.surf_to_texture(ui_surf)
            ui_tex.use(0)
            
            program = self.programs[1]
            
            program['tex'].value = 0
            program['time'].value = t
            
            self.render_objects[1].render(mode=moderngl.TRIANGLE_STRIP)
            
            ui_tex.release()

"""Build the GlassBlink group (BlinkScript replacement for the NukeSurvivalToolkit Glass gizmo).
Usable from nuke -t and from the live bridge. build_glass_blink(name, kernel_path) -> Group node."""
import os, nuke

KERNEL_DEFAULT = os.path.join(os.path.expanduser('~'), '.nuke', 'blinkscript', 'GlassRefract.blink')


def build_glass_blink(name='GlassBlink', kernel_path=KERNEL_DEFAULT, link=True):
    g = nuke.nodes.Group(name=name)
    g['tile_color'].setValue(0xcc804eff)
    with g:
        inp_img = nuke.nodes.Input(name='img')
        inp_ctl = nuke.nodes.Input(name='control')
        inp_mask = nuke.nodes.Input(name='mask')
        # control alpha -> all four channels so the kernel's .w is always defined
        sh = nuke.nodes.Shuffle2(name='ctrl_alpha', inputs=[inp_ctl])
        sh['in1'].setValue('alpha')
        sh['mappings'].setValue([('rgba.alpha', 'rgba.red'), ('rgba.alpha', 'rgba.green'),
                                 ('rgba.alpha', 'rgba.blue'), ('rgba.alpha', 'rgba.alpha')])
        bl = nuke.nodes.BlinkScript(name='GlassRefract', inputs=[inp_img, sh])
        # kernelSource.setValue() is a no-op on the BlinkEditorKnob from Python;
        # loading from file is the route that actually compiles.
        bl['kernelSourceFile'].setValue(kernel_path.replace('\\', '/'))
        bl['reloadKernelSourceFile'].execute()
        bl['useGPUIfAvailable'].setValue(True)
        bl['outputChannels'].setValue('rgba')
        for k in ('GlassRefract_src', 'GlassRefract_control'):
            if bl.knob(k):
                bl[k].setValue('rgba')
        # masked merge back onto the untouched stream (rgba only, nothing else leaks)
        mg = nuke.nodes.Merge2(name='Merge2', inputs=[inp_img, bl, inp_mask])
        mg['operation'].setValue('copy')
        mg['output'].setValue('rgba')
        out = nuke.nodes.Output(name='Output1', inputs=[mg])
        for i, n in enumerate((inp_img, inp_ctl, inp_mask, sh, bl, mg, out)):
            n.setXYpos(200 if n in (inp_ctl, sh) else 0, i * 60)
    # ---- user knobs, same names/labels as the original Glass gizmo ----
    g.addKnob(nuke.Tab_Knob('Glass', 'Glass'))
    k = nuke.Link_Knob('channles', 'channels'); k.setLink('Merge2.output'); g.addKnob(k)
    g.addKnob(nuke.Text_Knob('div0', ''))
    k = nuke.Double_Knob('displace', 'Displace'); k.setRange(0, 20); g.addKnob(k); k.setValue(1.6)
    k = nuke.Double_Knob('abberation', 'Abberation'); g.addKnob(k); k.setValue(0)
    k = nuke.Double_Knob('max_displace', 'max pull (px)'); k.setRange(1, 500); g.addKnob(k); k.setValue(64)
    k.setTooltip('Hard clamp on the refraction pull in pixels. The original gizmo had none and asked IDistort '
                 'for thousands of pixels at hard matte edges.')
    g.addKnob(nuke.Text_Knob('div1', 'Defocus'))
    k = nuke.Boolean_Knob('useDef', 'Apply Defocus'); k.setFlag(nuke.STARTLINE); g.addKnob(k); k.setValue(True)
    k = nuke.Double_Knob('size', 'size'); k.setRange(0, 20); g.addKnob(k); k.setValue(2.3)
    k = nuke.Double_Knob('max_size', 'maximum'); k.setRange(0, 64); g.addKnob(k); k.setValue(11.2)
    k = nuke.Double_Knob('shape', 'filter shape'); k.setRange(0, 1); g.addKnob(k); k.setValue(0.605)
    g.addKnob(nuke.Text_Knob('div2', ''))
    g.addKnob(nuke.Text_Knob('masklabel', 'mask', ''))
    for src_k, lab in (('maskChannelInput', ''), ('inject', 'inject'), ('invert_mask', 'invert'), ('fringe', 'fringe')):
        k = nuke.Link_Knob(src_k, lab); k.setLink('Merge2.' + src_k); k.clearFlag(nuke.STARTLINE); g.addKnob(k)
    k = nuke.Link_Knob('mix', 'mix'); k.setLink('Merge2.mix'); g.addKnob(k)
    g.addKnob(nuke.Text_Knob('div3', ''))
    k = nuke.Boolean_Knob('useGPU', 'use GPU if available'); k.setFlag(nuke.STARTLINE); g.addKnob(k); k.setValue(True)
    if link:
        link_params(g)
    return g


def link_params(g):
    """Wire kernel param knobs (created by Nuke after the GUI event loop ticks) to the group knobs."""
    bl = g.node('GlassRefract')
    links = {'GlassRefract_displace': 'parent.displace', 'GlassRefract_aberration': 'parent.abberation',
             'GlassRefract_maxDisplace': 'parent.max_displace', 'GlassRefract_useDefocus': 'parent.useDef',
             'GlassRefract_defocusSize': 'parent.size', 'GlassRefract_defocusMax': 'parent.max_size',
             'GlassRefract_defocusShape': 'parent.shape', 'useGPUIfAvailable': 'parent.useGPU'}
    missing = []
    for kn, expr in links.items():
        if bl.knob(kn):
            bl[kn].setExpression(expr)
        else:
            missing.append(kn)
    if missing:
        raise RuntimeError('BlinkScript param knobs not found (kernel compile failed?): %s ; knobs=%s'
                           % (missing, [x for x in bl.knobs() if x.startswith('GlassRefract')]))
    return g

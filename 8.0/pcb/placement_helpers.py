import math
from pcbnew import *


"""
import placement_helpers
placement_helpers.place_circle(placement_helpers.make_references('D', start_number=1, number=60), -90, (140,140), 60, component_offset=-90, hide_ref=True, lock=False)
"""

def move_modules_relative(references, relative_movement):
    pcb = GetBoard()
    for reference in references:
        part = pcb.FindFootprintByReference(reference)
        (xPos, yPos) = (ToMM(v) for v in part.GetPosition())
        part.SetPosition( VECTOR2I(FromMM(xPos+relative_movement[0]), FromMM(yPos+relative_movement[1])) )
    Refresh()
 
def place_circle(refdes, start_angle, center, radius, component_offset=0, hide_ref=True, lock=False, reverse_spin=None):
    """
    Places components in a circle
    refdes: List of component references
    start_angle: Starting angle
    center: Tuple of (x, y) mils of circle center
    radius: Radius of the circle in mils
    component_offset: Offset in degrees for each component to add to angle
    hide_ref: Hides the reference if true, leaves it be if None
    lock: Locks the footprint if true
    reverse_spin: If true, increments CCW instead of CW
    """
    pcb = GetBoard()
    deg_per_idx = 360.0 / len(refdes)
    if reverse_spin is None:
        reverse_spin = False
    if reverse_spin:
        deg_per_idx *= -1
    for idx, rd in enumerate(refdes):
        if rd is None:
          continue
        part = pcb.FindFootprintByReference(rd)
        angle = (deg_per_idx * idx + start_angle) % 360.0
        print('{0}: {1}'.format(rd, angle))
        xmils = center[0] + math.cos(math.radians(angle)) * radius
        ymils = center[1] + math.sin(math.radians(angle)) * radius
        part.SetPosition(VECTOR2I(FromMM(xmils), FromMM(ymils)))
        part.SetOrientationDegrees(-1*(angle+component_offset))
        if hide_ref is not None:
            part.Reference().SetVisible(not hide_ref)
    Refresh()
    
def place_concentric_circles(refdes, start_angle, center, component_width, circle_start_radius=3, circle_spacing=3, component_offset=0, hide_ref=True, lock=False):
    components_left = list(refdes)
    spacing = circle_spacing
    if spacing is None or spacing < 0:
        spacing = 3
    cur_radius = circle_start_radius
    if cur_radius is None or cur_radius < 0:
        cur_radius = 3
    while len(components_left) > 0:
        components_in_radius = (2*math.pi*cur_radius) / component_width
        while len(components_left) > components_in_radius and components_in_radius < 3:
            cur_radius+=1
            components_in_radius = (2*math.pi*cur_radius) / component_width
        components_in_radius = math.floor(components_in_radius)
        components_to_move, components_left = components_left[:components_in_radius], components_left[components_in_radius:]
        place_circle(components_to_move, start_angle, center, cur_radius, component_offset=component_offset, hide_ref=hide_ref, lock=lock)
        cur_radius += spacing
    
    
def place_clock(center=(100.0, 100.0), spacing=3.0, radius_start=30.0):
    minutes = ['D{}'.format(i+1) for i in range(60)]
    seconds = ['D{}'.format(i+61) for i in range(60)]
    hours = ['D{}'.format(i+121) for i in range(12)]
    minute_caps = ['C{}'.format(i+5) for i in range(10)]
    second_caps = ['C{}'.format(i+15) for i in range(10)]
    hour_caps = ['C{}'.format(i+25) for i in range(2)]
    place_circle(second_caps, -90.0, center, radius_start+(spacing*0), component_offset=-90.0)
    place_circle(seconds, -90.0, center, radius_start+(spacing*1))
    place_circle(minute_caps, -90.0, center, radius_start+(spacing*2), component_offset=-90.0)
    place_circle(minutes, -90.0, center, radius_start+(spacing*3))
    place_circle(hour_caps, -90.0, center, radius_start+(spacing*4), component_offset=-90.0)
    place_circle(hours, -90.0, center, radius_start+(spacing*5))
    
def place_hexclock(center=(100.0, 100.0), spacing= 3.0, radius_start=25.0, start_angle=-90.0):
    seconds = ['D{}'.format(i+1) for i in range(6)]
    minutes = ['D{}'.format(i+7) for i in range(6)]
    hours   = ['D{}'.format(i+13) for i in range(6)]
    place_circle(seconds, start_angle, center, radius_start-(spacing*1))
    place_circle(minutes, start_angle, center, radius_start-(spacing*2))
    place_circle(hours,   start_angle, center, radius_start-(spacing*3))
    
sevenSegDiodeLayout = [
  (-1.5,0), (-0.5,0), (0.5,0), (1.5,0),
  (-1.5,1),                    (1.5,1),
  (-1.5,2),                    (1.5,2),
  (-1.5,3), (-0.5,3), (0.5,3), (1.5,3),
  (-1.5,4),                    (1.5,4),
  (-1.5,5),                    (1.5,5),
  (-1.5,6), (-0.5,6), (0.5,6), (1.5,6)
]
sevenSegCapLayout = [
  (0, 0.1679790026),
  (0, 1.498687664),
  (0, 3),
  (0, 4.498687664),
  (0, 5.8346456693)
]

def make_references(prefix, start_number=1, number=1):
    return ['{}{}'.format(prefix, num+start_number) for num in range(number)]
    
def place_7_segment(upper_left=(100.0, 100.0), spacing=(2.54, 3.81), diodes=None, capacitors=None, layout=(sevenSegDiodeLayout, sevenSegCapLayout), refresh=True):
    if diodes is None or len(diodes) != 20:
        print("Diode list isn't quite right, expecting a list of exactly 20 diode references, got: {}".format(diodes))
        return
    if capacitors is None or len(capacitors) != 5:
        print("Capacitor list isn't quite right, expecting a list of exactly 5 capacitor references, got: {}".format(capacitors))
        return
    dLayout = layout[0]
    cLayout = layout[1]
    
    pcb = GetBoard()
    for i in range(len(diodes)):
        part = pcb.FindFootprintByReference(diodes[i])
        offset = dLayout[i]
        part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(spacing[0]))), FromMM(float(upper_left[1])+(float(offset[1])*float(spacing[1]))) ))
    for i in range(len(capacitors)):
        part = pcb.FindFootprintByReference(capacitors[i])
        offset = cLayout[i]
        part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(spacing[0]))), FromMM(float(upper_left[1])+(float(offset[1])*float(spacing[1]))) ))
    if refresh:
        Refresh()
        
colonDiodeLayout = [
    (-0.5,0), (0.5,0),
    (-0.5,1), (0.5,1),
    (-0.5,0), (0.5,0),
    (-0.5,1), (0.5,1),
]

colonCapLayout = [
    (0, 0.5),
    (0, 0.5)
]
        
def place_colon(upper_left=(100.0, 100.0), spacing=(2.54, 3.81), diodes=None, capacitors=None, layout=(colonDiodeLayout, colonCapLayout), refresh=True):
    if diodes is None or len(diodes) != 8:
        print("Diode list isn't quite right, expecting a list of exactly 8 diode references, got: {}".format(diodes))
        return
    if capacitors is None or len(capacitors) != 2:
        print("Capacitor list isn't quite right, expecting a list of exactly 2 capacitor references, got: {}".format(capacitors))
        return
    minSpacing = min(spacing)
    
    # The height of the top dot of the colon, in y spacing
    topHeight = 1.4015748031
    # Ditto for the bottom dot of the colon, in y spacing
    bottomHeight = 4.0682414698
    dLayout = layout[0]
    cLayout = layout[1]
    
    
    pcb = GetBoard()
    for i in range(4):
        part = pcb.FindFootprintByReference(diodes[i])
        offset = dLayout[i]
        part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(minSpacing))), FromMM(float(upper_left[1])+(float(offset[1])*float(minSpacing)) + (float(topHeight))*float(spacing[1])) ))
    for i in range(4, 8):
        part = pcb.FindFootprintByReference(diodes[i])
        offset = dLayout[i]
        part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(minSpacing))), FromMM(float(upper_left[1])+(float(offset[1])*float(minSpacing)) + (float(bottomHeight))*float(spacing[1])) ))
    part = pcb.FindFootprintByReference(capacitors[0])
    offset = cLayout[0]
    part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(minSpacing))), FromMM(float(upper_left[1])+(float(offset[1])*float(minSpacing)) + (float(topHeight))*float(spacing[1])) ))
    part = pcb.FindFootprintByReference(capacitors[1])
    offset = cLayout[1]
    part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(minSpacing))), FromMM(float(upper_left[1])+(float(offset[1])*float(minSpacing)) + (float(bottomHeight))*float(spacing[1])) ))
    
    if refresh:
        Refresh()
    
 
def place_7_segment_clock(upper_left=(100.0, 100.0), spacing=(2.54, 3.81), inter_digit_spacing=15.0, colon_spacing=0.0, diode_starts=(117, 97, 77, 57, 1, 21), capacitor_starts=(35, 30, 25, 20, 6, 11), colon_starts=(49, 41), colon_cap_starts=(18, 16)):
    if diode_starts is None or len(diode_starts) != 6:
        print("Diode list isn't quite right, expecting a list of exactly 6 diode reference numbers, got: {}".format(diode_starts))
        return
    if capacitor_starts is None or len(capacitor_starts) != 6:
        print("Capacitor list isn't quite right, expecting a list of exactly 6 capacitor reference numbers, got: {}".format(capacitor_starts))
        return
    if colon_starts is None or len(colon_starts) != 2:
        print("Capacitor list for colons isn't quite right, expecting a list of exactly 2 diode reference numbers, got: {}".format(colon_starts))
        return
    if colon_cap_starts is None or len(colon_cap_starts) != 2:
        print("Capacitor list for colons isn't quite right, expecting a list of exactly 2 capacitor reference numbers, got: {}".format(colon_cap_starts))
        return
    accumulator = 0
    for i in range(6):
        colon_remainder = i%2
        place_7_segment(
                upper_left=(upper_left[0]+accumulator, upper_left[1]),
                spacing=spacing,
                diodes=make_references("D", diode_starts[i], 20),
                capacitors=make_references("C", capacitor_starts[i], 5),
                refresh=False
        )
        if colon_remainder == 0:
            accumulator+=float(inter_digit_spacing)
        if colon_remainder == 1:
            accumulator+=float(colon_spacing)*2
    accumulator = float(inter_digit_spacing)+float(colon_spacing)
    for i in range(2):
        place_colon(
                upper_left=(upper_left[0]+accumulator, upper_left[1]),
                spacing=spacing,
                diodes=make_references("D", colon_starts[i], 8),
                capacitors=make_references("C", colon_cap_starts[i], 2),
                refresh=False
        )
        accumulator+=float(inter_digit_spacing)+float(colon_spacing)*2
    Refresh()
    
sevenSegEquidistantDiodeLayout = [
  (-0.5,0),   (0,0), (0.5,0),
  (-0.5,0.5),        (0.5,0.5),
  (-0.5,1),   (0,1), (0.5,1),
  (-0.5,1.5),        (0.5,1.5),
  (-0.5,2),   (0,2), (0.5,2)
]
    
def place_7_segment_equidistant(upper_left=(100.0, 100.0), spacing=(2.54, 3.81), diodes=None, layout=None, refresh=True):
    if layout is None:
        layout = sevenSegEquidistantDiodeLayout
    if diodes is None or len(diodes) != len(layout):
        print("Diode list isn't quite right, expecting a list of exactly {} diode references, got: {}".format(len(layout), diodes))
        return
    
    pcb = GetBoard()
    for i in range(len(diodes)):
        part = pcb.FindFootprintByReference(diodes[i])
        offset = layout[i]
        part.SetPosition(VECTOR2I( FromMM(float(upper_left[0])+(float(offset[0])*float(spacing[0]))), FromMM(float(upper_left[1])+(float(offset[1])*float(spacing[1]))) ))
    if refresh:
        Refresh()
    
def toggle_reference(parts, turn_on, turn_value_on=None):
    pcb = GetBoard()
    if turn_on is None:
        turn_on = True
    for ref in parts:
        part = pcb.FindFootprintByReference(ref)
        if part is not None:
            part.Reference().SetVisible(turn_on)
            if turn_value_on is not None:
                part.Value().SetVisible(turn_value_on)
    Refresh()
    
def rotate_parts(parts, angle):
    pcb = GetBoard()
    if angle is None:
        angle = 0
    for i in range(len(parts)):
        part = pcb.FindFootprintByReference(parts[i])
        part.SetOrientationDegrees( (part.GetOrientationDegrees() + 180) % 360 )
    Refresh()
    
def flip_parts(parts, rotate=None):
    pcb = GetBoard()
    if rotate is None:
        rotate = False
    for i in range(len(parts)):
        part = pcb.FindFootprintByReference(parts[i])
        part.Flip(part.GetCenter())
        if rotate:
            part.SetOrientationDegrees( (part.GetOrientationDegrees() + 180) % 360 )
    Refresh()
    
def place_grid(upper_left=(100.0, 100.0), spacing=(2.54, 2.54), grid_size=(8,8), parts=None, flip_every_second_row=False, rotate_every_second_row=False, default_orientation=0, blank_labels=False, increment_in_columns=False, rotate_grid=None):
    if parts is None:
        print("No components given")
        return
    if len(parts) > (grid_size[0]*grid_size[1]):
        print("Trying to lay too many parts into grid that is too small; tried to lay {} parts in a grid with {} positions".format(len(parts), (grid_size[0]*grid_size[1])))
        return
    left = upper_left[0] ## center of upper leftmost object, x
    top = upper_left[1] ## center of upper leftmost object, y
    x = spacing[0] ## distance between centerpoints, x
    y = spacing[1] ## distance between centerpoints, y
    columns = grid_size[0] ## How many columns in this grid
    rows = grid_size[1] ## How many rows in this grid
    gridRot = 0 if rotate_grid is None else float(rotate_grid) ## What orientation to offset the whole grid (rotating around the upper leftmost centerpoint)
    rad_convert = (math.pi/180) ## Convenience, to make radians from degrees
    
    pcb = GetBoard()
    for i in range(len(parts)):
        part = pcb.FindFootprintByReference(parts[i]) ## The part, as an object we can manipulate
        if increment_in_columns: ## Is the second part the next row from the first?
            column = int(i/rows)
            row = i%rows
        else: ## Or the next column
            row = int(i/columns)
            column = i%columns
        
        ## If we're flipping every second row, that means we need to invert the placement orientation
        ## (instead of placing at x=0, we place at x=max-1, instead of x=1, x=max-2, etc)
        if flip_every_second_row and (row % 2) == 1:
            column = columns - column - 1
		## To make rotating the grid easier, convert everything to polar coordinates
        x_dist = x*column
        y_dist = y*row
        dist = math.sqrt(x_dist**2 + y_dist**2)
        angle = math.atan2(y_dist, x_dist)
        
        ## ... and add our grid rotation ...
        result_angle = angle+(gridRot*rad_convert)
        
        ## then convert back to cartesian to place the component
        xPos = left + (math.cos(result_angle)*dist)
        yPos = top + (math.sin(result_angle)*dist)
        part.SetPosition(VECTOR2I( FromMM(xPos), FromMM(yPos) ))
        
        ## Rotate the component if requested
        part.SetOrientationDegrees( ((default_orientation-gridRot) % 360) )
        
        if flip_every_second_row and ( (not increment_in_columns and (row % 2) == 1) or (increment_in_columns and (column % 2) == 1) ):
            part.SetOrientationDegrees( ((default_orientation-gridRot+180) % 360) );
        if rotate_every_second_row and ( (not increment_in_columns and (row % 2) == 1) or (increment_in_columns and (column % 2) == 1) ):
            part.SetOrientationDegrees( ((default_orientation-gridRot+180) % 360) );
        if blank_labels:
            part.Reference().SetVisible(False)
    Refresh()

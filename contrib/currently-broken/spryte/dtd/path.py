Blocker = object()
Start = False
End = object()

class Path(dict):
    @classmethod
    def determine_path(cls, field, width, height):
        path = cls()
        path.width = width
        path.height = height
        path.ends = set()
        path.starts = []
        cells = []
        for y in range(height):
            m = []
            for x in range(width):
                cell = field[x, y]
                if cell is End:
                    path[x, y] = 0
                    cells.append((x, y))
                    path.ends.add((x, y))
                elif cell is Blocker:
                    path[x, y] = Blocker
                elif cell is Start:
                    path.starts.append((x, y))
        #path.dump()

        x_extent = path.width-1
        y_extent = path.height-1
        while cells:
            new = []
            for x, y in cells:
                v = path[x, y]
                if x > 0 and (x-1, y) not in path:
                    path[x-1, y] = v + 1
                    new.append((x-1, y))
                if x < x_extent and (x+1, y) not in path:
                    path[x+1, y] = v + 1
                    new.append((x+1, y))
                if y > 0 and (x, y-1) not in path:
                    path[x, y-1] = v + 1
                    new.append((x, y-1))
                if y < y_extent and (x, y+1) not in path:
                    path[x, y+1] = v + 1
                    new.append((x, y+1))
            cells = new

        for k in list(path.keys()):
            if path[k] is Blocker or path[k] is None:
                del path[k]
        return path

    def dump(self, mods={}):
        import sys
        for y in range(self.height):
            sys.stdout.write('%02d '%y)
            for x in range(self.width):
                p = (x, y)
                if p in mods:
                    c = '*'
                else:
                    c = self.get(p)
                    if c is None:
                        c = '.'
                    elif c is Blocker:
                        c = '#'
                    else:
                        c = chr(c + ord('0'))
                sys.stdout.write(c)
            print
        print
        print '   ',
        for i in range(self.width):
            sys.stdout.write('%d'%(i%10))
        print

    def get_neighbors(self, x, y):
        '''May move horizontal, vertical or diagonal as long as there's not
        a blocker on both sides of the diagonal.
        '''
        l = []

        # top left
        if x > 0 and y < self.height-1:
            tx = x - 1; ty = y + 1
            if (x, ty) in self and (tx, y) in self and (tx, ty) in self:
                l.append((self[tx, ty], (tx, ty)))
        # top right
        if x < self.width-1 and y < self.height-1:
            tx = x + 1; ty = y + 1
            if (x, ty) in self and (tx, y) in self and (tx, ty) in self:
                l.append((self[tx, ty], (tx, ty)))
        # bottom left
        if x > 0 and y > 0:
            tx = x - 1; ty = y - 1
            if (x, ty) in self and (tx, y) in self and (tx, ty) in self:
                l.append((self[tx, ty], (tx, ty)))
        # bottom right
        if x < self.width-1 and y > 0:
            tx = x + 1; ty = y - 1
            if (x, ty) in self and (tx, y) in self and (tx, ty) in self:
                l.append((self[tx, ty], (tx, ty)))

        # left
        if x > 0:
            tx = x - 1
            if (tx, y) in self:
                l.append((self[tx, y], (tx, y)))
        # right
        if x < self.width-1:
            tx = x + 1
            if (tx, y) in self:
                l.append((self[tx, y], (tx, y)))
        # left
        if y > 0:
            ty = y - 1
            if (x, ty) in self:
                l.append((self[x, ty], (x, ty)))
        # right
        if y < self.height-1:
            ty = y + 1
            if (x, ty) in self:
                l.append((self[x, ty], (x, ty)))

        l.sort()
        return l

    def next_step(self, x, y):
        return self.get_neighbors(x, y)[0][1]

    def test_mod(self, set_cells):
        '''Determine whether the map would be solvable if the cells
        provided are blocked.
        '''
        set_cells = set(set_cells)
        current = self.starts
        visited = set()
        while current:
            visited |= set(current)
            #print 'TRY', current
            #print 'VISITED', visited
            next = set()
            for x, y in current:
                options = self.get_neighbors(x, y)
                options.reverse()
                #print 'VISIT', (x, y), options
                while options:
                    c = options.pop()
                    p = c[1]
                    if p in self.ends:
                        #print 'END', p
                        return True
                    if p not in set_cells and p not in visited:
                        next.add(p)
                        break
            current = list(next)
        return False

if __name__ == '__main__':
    field_cells = '''
++++SSS+++++
+####.#####+
+#........#+
S#.......##E
S..........E
S#.......##E
+#..###...#+
+####.#####+
++++EEE+++++
'''.strip()

    field_rows = [line.strip() for line in field_cells.splitlines()]
    height = len(field_rows)
    width = len(field_rows[0])

    play_field = {}
    for y, line in enumerate(field_rows):
        for x, cell in enumerate(line):
            if cell == '#':
                content = Blocker
            else:
                if cell == 'E':
                    content = End
                elif cell == 'S':
                    content = Start
                elif cell == '+':
                    content = Blocker
                else:
                    content = None
            play_field[x*2, y*2] = content
            play_field[x*2+1, y*2] = content
            play_field[x*2, y*2+1] = content
            play_field[x*2+1, y*2+1] = content

    path = Path.determine_path(play_field, width*2, height*2)
    path.dump()
    
    print path.get_neighbors(7, 13)

    print 'TEST BLOCKING MODS'
    path.dump(set(((18, 8), (19, 8), (18, 9), (19, 9))))
    assert path.test_mod(()) == True
    assert path.test_mod(((18, 8), (19, 8), (18, 9), (19, 9))) == False
    assert path.test_mod(((0, 8), (0, 8), (1, 9), (1, 9))) == True


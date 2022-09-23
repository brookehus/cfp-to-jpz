# Brooke Husic
# Created 9/23/2022
# Last updated 9/23/2022
# Instructions:
# >>> python cfp-to-jpz my_cfp.cfp

import os
import sys
import numpy as np


class Crossword():
    """Loads in a .cfp file and organizes its info."""

    def __init__(self, cfp_filename):
        self.cfp_filename = cfp_filename

        self.metadata_dict = self.get_metadata()
        self.grid = self.get_grid()
        self._rebus_dict = self.get_rebus_dict()
        self._numbering = self.get_numbering()

        # the answer dict will have rebus codes, if applicable
        self._answer_dict = self.get_answer_dict()
        self.clue_dict = self.get_clue_dict()
        self.ans_clue_dict = self.get_answer_clue_dict()
        self._location_dict = self.get_location_dict()

    def get_metadata(self):
        metadata_dict = {
            'title': '',
            'author': '',
            'copyright': '',
            'notes': ''
        }

        with open(self.cfp_filename, 'r') as cfp_file:
            for i, row in enumerate(cfp_file):
                if row[1:6] == 'TITLE':
                    title = row.lstrip('<TITLE>').rstrip('</TITLE>\n')
                    metadata_dict['title'] = title

                elif row[1:7] == 'AUTHOR':
                    author = row.lstrip('<AUTHOR>').rstrip('</AUTHOR>\n')
                    metadata_dict['author'] = author

                elif row[1:10] == 'COPYRIGHT':
                    copyright = row.lstrip(
                        '<COPYRIGHT>').rstrip('</COPYRIGHT>\n')
                    metadata_dict['copyright'] = copyright

                elif row[1:6] == 'NOTES':
                    notes = row.lstrip('<NOTES>').rstrip('</NOTES>\n')
                    metadata_dict['notes'] = notes

        return metadata_dict

    def get_grid(self):
        with open(self.cfp_filename, 'r') as cfp_file:
            grid = []

            # assumes grid image is the only part of a cfp
            # file whose line doesn't start with '<'
            for i, row in enumerate(cfp_file):
                if row[0] != '<':
                    grid.append(row.rstrip('\n'))

        self.n_rows = len(grid)
        self.n_cols = len(grid[0])

        self._grid_letters = np.array([list(grid[i])
                                       for i in range(len(grid))])

        return grid

    def get_rebus_dict(self):
        rebus_dict = {}

        with open(self.cfp_filename, 'r') as cfp_file:

            # assumes cfp convention e.g.:
            # <REBUS display="R" input="@" letters="rose"/>
            for i, row in enumerate(cfp_file):
                if row[1:14] == 'REBUS display':
                    rebus_raw = row.rstrip('/>\n')
                    rebus_info = '='.join(
                        rebus_raw.split(' ')).split('=')
                    rebus_dict[rebus_info[4].strip(
                        '""')] = rebus_info[6].strip('""').upper()

        if len(rebus_dict) == 0:
            self.rebus = False
        else:
            self.rebus = True

        return rebus_dict

    def get_numbering(self):
        numbering = np.zeros((self.n_rows, self.n_cols), dtype=int)
        for i, row in enumerate(self._grid_letters):
            for j, letter in enumerate(row):
                if letter == '.':
                    numbering[i, j] = -1

        across_nums = []
        down_nums = []

        count = 1
        for i, top_slot in enumerate(numbering[0]):
            if top_slot == 0:
                numbering[0, i] = count
                down_nums.append(count)
                if numbering[0][i-1] == -1 or i == 0:
                    across_nums.append(count)
                count += 1

        for i, row in enumerate(numbering):
            for j, num in enumerate(row):
                if i == 0:
                    continue
                elif j == 0 and num > -1:
                    numbering[i, j] = count
                    across_nums.append(count)
                    if numbering[i-1, j] == -1:
                        down_nums.append(count)
                    count += 1
                else:
                    # is this the start of a down clue
                    if num == 0 and numbering[i-1, j] == -1:
                        numbering[i, j] = count
                        down_nums.append(count)
                        # ... and an across clue?
                        if numbering[i, j-1] == -1:
                            across_nums.append(count)
                        count += 1
                    # is this the start of an across clue
                    elif num == -1 and j < self.n_cols-1:
                        if numbering[i, j+1] > -1:
                            numbering[i, j+1] = count
                            across_nums.append(count)
                            # ... and a down clue?
                            if numbering[i-1, j+1] == -1:
                                down_nums.append(count)
                            count += 1

        across_starts = []
        for row in numbering:
            this_row = []
            for i, num in enumerate(row[:self.n_rows]):
                if i == 0 and num > -1:
                    this_row.append(num)
                elif row[i-1] == -1:
                    if num > -1:
                        this_row.append(num)
            across_starts.append(this_row)

        down_starts = []
        for col in numbering.T:
            this_col = []
            for i, num in enumerate(col[:self.n_cols]):
                if i == 0 and num > -1:
                    this_col.append(num)
                elif col[i-1] == -1:
                    if num > -1:
                        this_col.append(num)
            down_starts.append(this_col)

        grid_flip = [''.join([row[i] for row in self.grid])
                     for i in range(len(self.grid))]

        across_words = [row.split('.') for row in self.grid]
        across_words = [[b for b in a if len(b) > 0] for a in across_words]

        down_words = [row.split('.') for row in grid_flip]
        down_words = [[b for b in a if len(b) > 0] for a in down_words]

        assert len(across_words) == self.n_rows
        assert len(across_starts) == self.n_rows
        assert len(down_words) == self.n_cols
        assert len(down_starts) == self.n_cols

        self._across_nums = across_nums
        self._across_starts = across_starts
        self._across_words = across_words

        self._down_nums = down_nums
        self._down_starts = down_starts
        self._down_words = down_words

        return numbering

    def get_answer_dict(self):
        answer_dict = {
            'across': {},
            'down': {}
        }
        for i, start_row in enumerate(self._across_starts):
            for j, num in enumerate(start_row):
                answer_dict['across'][num] = self._across_words[i][j]

        down_dict = {}
        for i, start_row in enumerate(self._down_starts):
            for j, num in enumerate(start_row):
                answer_dict['down'][num] = self._down_words[i][j]

        assert len(answer_dict['across']) == len(self._across_nums)
        assert len(answer_dict['down']) == len(self._down_nums)

        return answer_dict

    def get_clue_dict(self):
        with open(self.cfp_filename, 'r') as cfp_file:
            clues_raw = []

            # assumes clues are of the form
            # <WORD dir="ACROSS" id="0" isTheme="false" num="1">[Clue]</WORD>
            for i, row in enumerate(cfp_file):
                if row[1:9] == 'WORD dir':
                    clues_raw.append(row.rstrip('</WORD>\n'))

            clue_dict = {}
            clue_dict['across'] = {}
            clue_dict['down'] = {}

            for raw_info in clues_raw:
                try:
                    clue_info, clue = raw_info.split('>')
                except:
                    clue_info = raw_info
                    clue = ''

                clue_info = clue_info.split('"')
                dir_ = clue_info[1].lower()
                num_ = int(clue_info[7])
                clue_dict[dir_][num_] = clue

        return clue_dict

    def get_answer_clue_dict(self):
        ans_clue_dict = {}
        for dir_ in ['across', 'down']:
            for k in sorted(self.clue_dict[dir_].keys()):
                ans = self._answer_dict[dir_][k]

                # replace rebus codes with strings
                if any(char in ans for char in self._rebus_dict.keys()):
                    new_ans = []
                    for char in ans:
                        if char in self._rebus_dict.keys():
                            new_ans.append(self._rebus_dict[char])
                        else:
                            new_ans.append(char)
                    ans = ''.join(new_ans)

                clue = self.clue_dict[dir_][k]
                if ans not in ans_clue_dict.keys():
                    ans_clue_dict[ans] = clue
                else:
                    raise ValueError(
                        '{} already in answer-clue dictionary'.format(ans)
                    )

        return ans_clue_dict

    def get_location_dict(self):
        location_dict = {}
        for i, row in enumerate(self._numbering):
            for j, char in enumerate(row):
                if char > 0:
                    location_dict[char] = [i, j]

        return location_dict


class Jpz():
    """Formats the jpz and has a method to write it to a file."""

    def __init__(self, crossword, pretty=True):
        self._xw = crossword
        self.pretty = pretty

        if pretty:
            self.lb = '\n'
            self.tab = '\t'
        else:
            self.lb = ''
            self.tab = ''

        self.metadata_strings = self.encode_metadata()
        self.grid_strings = self.encode_grid()
        self.location_strings = self.encode_locations()
        self.clue_strings = self.encode_clues()

    def encode_metadata(self):
        metadata_strings = []

        metadata_strings.append(
            '<?xml version="1.0" encoding="UTF-8"?>{}{}'.format(
                self.lb, self.lb)
        )

        # why does it need these hyperlinks? i do not know
        metadata_strings.append(
            '<crossword-compiler xmlns="http://crossword.info/xml/crossword-compiler">{}{}<rectangular-puzzle xmlns="http://crossword.info/xml/rectangular-puzzle" alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ">{}'.format(
                self.lb, self.tab, self.lb)
        )

        metadata_strings.append(
            '{}{}<metadata>{}{}{}{}<title>{}</title>{}'.format(
                self.tab, self.tab, self.lb,
                self.tab, self.tab, self.tab,
                self._xw.metadata_dict['title'], self.lb
            )
        )

        metadata_strings.append(
            '{}{}{}<creator>{}</creator>{}'.format(
                self.tab, self.tab, self.tab,
                self._xw.metadata_dict['author'], self.lb
            )
        )

        metadata_strings.append(
            '{}{}{}<copyright>{}</copyright>{}'.format(
                self.tab, self.tab, self.tab,
                self._xw.metadata_dict['copyright'], self.lb
            )
        )

        metadata_strings.append(
            '{}{}{}<description>{}</description>{}{}{}</metadata>{}{}'.format(
                self.tab, self.tab, self.tab,
                self._xw.metadata_dict['notes'], self.lb,
                self.tab, self.tab, self.lb, self.lb
            )
        )

        return metadata_strings

    def encode_grid(self):
        grid_strings = []

        grid_strings.append(
            '<grid height="{}" width="{}">{}{}'.format(
                self._xw.n_rows, self._xw.n_cols, self.lb, self.lb)
        )

        for i, row in enumerate(self._xw._numbering):
            for j, k in enumerate(row):
                if k == -1:
                    grid_strings.append(
                        '<cell x="{}" y="{}" type="block" />{}'.format(
                            j+1, i+1, self.lb)
                    )
                else:
                    if self._xw.grid[i][j] in self._xw._rebus_dict.keys():
                        char = self._xw._rebus_dict[self._xw.grid[i][j]]
                    else:
                        char = self._xw.grid[i][j]

                    if k == 0:
                        grid_strings.append(
                            '<cell x="{}" y="{}" solution="{}" />{}'.format(
                                j+1, i+1, char, self.lb)
                        )
                    else:
                        grid_strings.append(
                            '<cell x="{}" y="{}" solution="{}" number="{}" />{}'.format(
                                j+1, i+1, char, k, self.lb)
                        )

        # italian style! that option can def just be deleted altogether. so can thick-border.
        grid_strings.append(
            '{}<grid-look cell-size-in-pixels="26" clue-square-divider-width="0.7" italian-style="false" numbering-scheme="normal" thick-border="true" />{}{}</grid>{}{}'.format(
                self.lb, self.lb, self.lb, self.lb, self.lb)
        )

        return grid_strings

    def encode_locations(self):
        location_strings = []

        cat_across_starts = sorted(list(np.concatenate(self._xw._across_starts)))
        cat_down_starts = sorted(list(np.concatenate(self._xw._down_starts)))

        for a in range(1, np.max(self._xw._numbering)+1):
            if a in cat_across_starts:
                location_strings.append(
                    '<word id="{}0000">{}'.format(a, self.lb))
                for i in range(len(self._xw._answer_dict['across'][a])):
                    location_strings.append(
                        '{}<cells x="{}" y="{}" />{}'.format(
                            self.tab,
                            self._xw._location_dict[a][1]+1+i,
                            self._xw._location_dict[a][0]+1,
                            self.lb
                        )
                    )
                location_strings.append('</word>{}'.format(self.lb))

            if a in cat_down_starts:
                location_strings.append(
                    '<word id="{}0001">{}'.format(a, self.lb))
                for i in range(len(self._xw._answer_dict['down'][a])):
                    location_strings.append(
                        '{}<cells x="{}" y="{}" />{}'.format(
                            self.tab,
                            self._xw._location_dict[a][1]+1,
                            self._xw._location_dict[a][0]+1+i,
                            self.lb
                        )
                    )
                location_strings.append('</word>{}'.format(self.lb))

        return location_strings

    def encode_clues(self):
        clue_strings = []

        clue_strings.append(
            '{}{}<clues ordering=""><title>Across</title>{}{}'.format(
                self.lb, self.lb, self.lb, self.lb)
        )

        # I've copied over the word id scheme from CMS, but it doesn't have to
        # be this way. For whatever reason, across clues get 0000 appended and
        # down clues get 0001 appended.
        for clue_num, clue in self._xw.clue_dict['across'].items():
            clue_strings.append(
                '<clue number="{}" word="{}0000">{}'.format(
                    clue_num, clue_num, self.lb)
            )
            clue_strings.append(
                '{}<span>{}</span>{}</clue>{}'.format(
                    self.tab, clue, self.lb, self.lb)
            )

        clue_strings.append(
            '{}</clues>{}{}<clues ordering=""><title>Down</title>{}{}'.format(
                self.lb, self.lb, self.lb, self.lb, self.lb)
        )

        for clue_num, clue in self._xw.clue_dict['down'].items():
            clue_strings.append(
                '<clue number="{}" word="{}0001">{}'.format(
                    clue_num, clue_num, self.lb)
            )
            clue_strings.append(
                '{}<span>{}</span>{}</clue>{}'.format(
                    self.tab, clue, self.lb, self.lb)
            )

        clue_strings.append(
            '{}</clues>{}{}'.format(
                self.lb, self.lb, self.lb)
        )

        return clue_strings

    def write_jpz(self, filename):
        """Write the .jpz to a file"""

        if filename[-4:] == '.cfp':
            jpz_filename = filename[:-4] + '.jpz'
        elif filename[-4:] != '.jpz':
            jpz_filename = filename + '.jpz'
        else:
            jpz_filename = filename

        # omg a while loop :o
        while os.path.exists(jpz_filename):
            jpz_filename = jpz_filename[:-4] + '-1' + '.jpz'

        with open(jpz_filename, 'w') as jpz_file:
            # write metadata
            for line in self.metadata_strings:
                jpz_file.write(line)

            # write prelude
            jpz_file.write(
                '<crossword>{}{}'.format(self.lb, self.lb)
            )

            # write grid
            for line in self.grid_strings:
                jpz_file.write(line)

            # write locations
            for line in self.location_strings:
                jpz_file.write(line)

            # write clues
            for line in self.clue_strings:
                jpz_file.write(line)

            # write coda
            jpz_file.write(
                '</crossword>{}{}</rectangular-puzzle>{}{}</crossword-compiler>\n'.format(
                    self.lb, self.lb, self.lb, self.lb)
            )

            print('Written to {}'.format(jpz_filename))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('    python cfp-to-jpz [cfp file]')
        sys.exit(0)
    else:
        cfp_filename = sys.argv[1]

        crossword = Crossword(cfp_filename)
        jpz = Jpz(crossword, pretty=True)
        jpz.write_jpz(cfp_filename)

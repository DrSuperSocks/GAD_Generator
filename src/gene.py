#!/usr/bin/env python

import math
import sys
from feature_tbl_entry import FeatureTblEntry

def length_of_segment(index_pair):
    return math.fabs(index_pair[1] - index_pair[0]) + 1

def trimmed_completely(gene_inds, seq_inds):
    return seq_inds == [0,0] or gene_inds[0] > seq_inds[1] or gene_inds[1] < seq_inds[0]

class Gene:

    def __init__(self, seq_name, source, indices, strand, identifier, name, score=None):
        self.seq_name = seq_name
        self.source = source
        self.indices = indices
        self.score = score
        self.strand = strand
        self.identifier = identifier
        self.name = name
        self.mrnas = []

    def __str__(self):
        result = "Gene (ID=" + str(self.identifier) + ", Name="
        result += self.name + ", seq_name=" + self.seq_name
        result += ") containing " + str(len(self.mrnas))
        result += " mrnas"
        return result

    def is_empty(self):
        return self.indices == [0, 0]

    def length(self):
        return length_of_segment(self.indices)

    def get_score(self):
        if self.score:
            return self.score
        else:
            return '.'

    def add_mrna(self, mrna):
        self.mrnas.append(mrna)

    def contains_mrna_named(self, name):
        for mrna in self.mrnas:
            if mrna.name == name:
                return True
        return False

    def remove_mrnas_with_cds_shorter_than(self, min_length):
        # TODO for now this also removes mrnas with NO cds, but do we want that?
        print("removing mrnas at gene " + self.name)
        to_remove = []
        if self.mrnas:
            for mrna in self.mrnas:
                print("now at mrna " + mrna.name)
                if mrna.cds:
                    print("it has a cds")
                    print("cds length is " + str(mrna.cds.length()))
                    if mrna.cds.length() < min_length:
                        print("okay, we're gonna have to remove " + mrna.name)
                        to_remove.append(mrna)
                else:
                    to_remove.append(mrna)
        print("mrnas to remove from this gene: " + str(to_remove))
        for m in to_remove:
            self.mrnas.remove(m)
        print("mrnas left on this gene: " + str(self.mrnas))

    def trim_end(self, endindex):
        if self.indices[0] > endindex:
            self.indices[0] = 0
            self.indices[1] = 0
        elif self.indices[1] > endindex:
            self.indices[1] = endindex
            for mrna in self.mrnas:
                mrna.trim_end(endindex)

    # beginindex is the new start index of sequence
    def trim_begin(self, beginindex):
        self.adjust_indices(-beginindex + 1)

    def clean_up_indices(self):
        if self.indices[1] < 1:
            self.indices[0] = 0
            self.indices[1] = 0
        elif self.indices[0] < 1:
            self.indices[0] = 1
        for mrna in self.mrnas:
            mrna.clean_up_indices()

    def remove_invalid_features(self):
        # remove mrnas with indices[0] == 0
        self.mrnas = [m for m in self.mrnas if m.indices[0] != 0]
        for mrna in self.mrnas:
            mrna.remove_invalid_features()

    def length_of_shortest_cds_segment(self):
        min_length = self.mrnas[0].length_of_shortest_cds_segment()
        if len(self.mrnas) == 1:
            return min_length
        else:
            for mrna in self.mrnas:
                if mrna.length_of_shortest_cds_segment() < min_length:
                    min_length = mrna.length_of_shortest_cds_segment()
        return min_length

    def collidesRange(self, start, stop):
        if start <= self.indices[1] and stop >= self.indices[0]:
            return True
        return False

    def adjust_indices(self, n):
        self.indices = [i + n for i in self.indices]
        for mrna in self.mrnas:
            mrna.adjust_indices(n) 

    def trim(self, new_indices):
        if trimmed_completely(self.indices, new_indices):
            self.mrnas = []
            self.indices = [0, 0]
        else:
            self.trim_end(new_indices[1])
            self.trim_begin(new_indices[0])
            for mrna in self.mrnas:
                mrna.adjust_phase()
            self.clean_up_indices()
            self.remove_invalid_features()

    def to_gff(self):
        result = self.seq_name + "\t" + self.source + "\t"
        result += 'gene' + "\t" + str(self.indices[0]) + "\t"
        result += str(self.indices[1]) + "\t" + self.get_score()
        result += "\t" + self.strand + "\t" + "." + "\t"
        result += "ID=" + str(self.identifier) + ";Name=" + self.name + "\n"
        for mrna in self.mrnas:
            result += mrna.to_gff(self.seq_name, self.source, self.strand)
        return result

    def to_tbl_entries(self):
        entries = []
        geneEntry = FeatureTblEntry()
        geneEntry.set_type("gene")
        geneEntry.set_name(self.name)
        geneEntry.set_seq_name(self.seq_name)
        geneEntry.add_coordinates(self.indices[0], self.indices[1])
        geneEntry.set_strand(self.strand)
        geneEntry.set_phase(0)
        geneEntry.set_partial_info(True, True) # Pretend there's a start and stop codon for genes
        entries.append(geneEntry)   
        for mrna in self.mrnas: 
            mrna_entries = mrna.to_tbl_entries(self.strand)
            for mrna_entry in mrna_entries:
                mrna_entry.set_seq_name(self.seq_name)
                entries.append(mrna_entry)
        return entries




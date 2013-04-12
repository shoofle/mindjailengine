#!/usr/bin/env python

import sys, getopt
import math

""" This is just a helper script to generate a .obj file for a z-axis-aligned cylinder, with a specified radius, thickness, and number of points around the outside. """

def print_help():
	print "generate_vertex_data -o output_file -r radius -t thickness -n number_of_points"
	sys.exit(2)

try: 
	options, other_arguments = getopt.getopt(sys.argv[1:], "o:r:t:n:", ["output=","radius=","thickness=","number_of_points=","outline_cap="])
except getopt.GetoptError:
	print_help()

cap_outline=-1

for opt, value in options:
	if opt in ('-o', '--output'): out_file_name = value
	elif opt in ('-r', '--radius'): radius = float(value)*1.0
	elif opt in ('-t', '--thickness'): thickness = float(value)/2.0
	elif opt in ('-n', '--number_of_points'): number_of_points = int(value)
	elif opt == '--outline_cap': cap_outline = int(value)
	else: print_help()

top_vertices, bottom_vertices = [], []
edge_normals = []
edge_top_texture_coordinates, edge_bottom_texture_coordinates = [], []
cap_top_texture_coordinates, cap_bottom_texture_coordinates = [], []
for i in range(number_of_points):
	top_vertices.append( (radius * math.cos(i*math.pi*2/number_of_points), radius * math.sin(i*math.pi*2/number_of_points), thickness) )
	bottom_vertices.append( (radius * math.cos(i*math.pi*2/number_of_points), radius * math.sin(i*math.pi*2/number_of_points), -thickness) )
	edge_normals.append( (math.cos(i*math.pi*2/number_of_points), math.sin(2*math.pi*2/number_of_points), 0) )
	edge_top_texture_coordinates.append(	[radius * math.pi*2 * i / number_of_points, 0] )
	edge_bottom_texture_coordinates.append( [radius * math.pi*2 * i / number_of_points, thickness] )
	cap_top_texture_coordinates.append(		[radius * math.cos(i*math.pi*2/number_of_points) + radius, radius * math.sin(i*math.pi*2/number_of_points) + thickness + radius] )
	cap_bottom_texture_coordinates.append(	[radius * math.cos(i*math.pi*2/number_of_points)+3*radius+thickness, radius * math.sin(i*math.pi*2/number_of_points) + thickness + radius] )

texture_coordinates = edge_top_texture_coordinates + edge_bottom_texture_coordinates + cap_top_texture_coordinates + cap_bottom_texture_coordinates
max_coord = max(max(map(lambda x: x[0], texture_coordinates)), max(map(lambda x: x[1], texture_coordinates)))
for vt in texture_coordinates: 
	vt[:] = [i*1.0/max_coord for i in vt]

top_cap_normal = (0, 0, 1)
bottom_cap_normal = (0, 0, -1)

faces_one, faces_two = [], []
normals_one, normals_two = [], []
faces_cap_top, faces_cap_bot = [], []

face_one_texture_indices, face_two_texture_indices = [], []
cap_top_texture_indices, cap_bottom_texture_indices = [], []
for i in range(number_of_points):
	faces_one.append( [ i,						number_of_points+i,							(i+1)%number_of_points ] )
	faces_two.append( [(i+1)%number_of_points,	number_of_points+i,		number_of_points + ((i+1)%number_of_points)] )
	normals_one.append( [ i,						i,		(i+1)%number_of_points ] )
	normals_two.append( [(i+1)%number_of_points,	i,		(i+1)%number_of_points ] )
	if cap_outline == -1:
		faces_cap_top.append( [0, (i+1)%number_of_points, i] )
		faces_cap_bot.append( [number_of_points, number_of_points + i, number_of_points + ((i+1)%number_of_points)] )
	else:
		faces_cap_top.append( [i, (i+cap_outline)%number_of_points, (i+1)%number_of_points] )
		faces_cap_bot.append( [number_of_points + i, number_of_points + ((i+1)%number_of_points), number_of_points + ((i+cap_outline)%number_of_points)] )
	
	face_one_texture_indices.append( faces_one[i][:] )
	face_two_texture_indices.append( faces_two[i][:] )

	offset = len(edge_top_texture_coordinates + edge_bottom_texture_coordinates)
	cap_top_texture_indices.append( [offset + j for j in faces_cap_top[i]] )
	cap_bottom_texture_indices.append( [offset + j for j in faces_cap_bot[i]] )
	
	

top_cap_normal_index = len(edge_normals)+1
top_cap_normal_indexes = [top_cap_normal_index, ]*3
bottom_cap_normal_index = len(edge_normals)+1+1
bottom_cap_normal_indexes = [bottom_cap_normal_index, ]*3


for indices in faces_one + faces_two + normals_one + normals_two + faces_cap_top + faces_cap_bot + face_one_texture_indices + face_two_texture_indices + cap_top_texture_indices + cap_bottom_texture_indices:
	indices[0] = indices[0]+1
	indices[1] = indices[1]+1
	indices[2] = indices[2]+1

with open(out_file_name, 'w') as f:
	f.write('# Vertices along the top edge.\n')
	for vert in top_vertices:
		f.write('v {0[0]} {0[1]} {0[2]}\n'.format(vert))

	f.write('# Vertices along the bottom edge.\n')
	for vert in bottom_vertices:
		f.write('v {0[0]} {0[1]} {0[2]}\n'.format(vert))
	
	f.write('# Normals along the edge.\n')
	for norm in edge_normals:
		f.write('vn {0[0]} {0[1]} {0[2]}\n'.format(norm))
	
	f.write('# Texture coordinates for the edge.\n')
	for tex in edge_top_texture_coordinates + edge_bottom_texture_coordinates:
		f.write('vt {0[0]} {0[1]}\n'.format(tex))
	f.write('# Texture coordinates for the caps.\n')
	for tex in cap_top_texture_coordinates + cap_bottom_texture_coordinates:
		f.write('vt {0[0]} {0[1]}\n'.format(tex))
	
	f.write('# Top cap normal.\n')
	f.write('vn {0[0]} {0[1]} {0[2]}\n'.format(top_cap_normal))
	f.write('# Bottom cap normal.\n')
	f.write('vn {0[0]} {0[1]} {0[2]}\n'.format(bottom_cap_normal))

	f.write('# Faces! Along the edge.\n')
	for face, tex, normal in zip(faces_one, face_one_texture_indices, normals_one):
		f.write('f {0[0]}/{1[0]}/{2[0]} {0[1]}/{1[1]}/{2[1]} {0[2]}/{1[2]}/{2[2]}\n'.format(face, tex, normal))
	for face, tex, normal in zip(faces_two, face_two_texture_indices, normals_two):
		f.write('f {0[0]}/{1[0]}/{2[0]} {0[1]}/{1[1]}/{2[1]} {0[2]}/{1[2]}/{2[2]}\n'.format(face, tex, normal))
	
	f.write('# Faces at the top.\n')
	for face, tex in zip(faces_cap_top, cap_top_texture_indices):
		f.write('f {0[0]}/{1[0]}/{2[0]} {0[1]}/{1[1]}/{2[1]} {0[2]}/{1[2]}/{2[2]}\n'.format(face, tex, top_cap_normal_indexes))

	f.write('# Faces at the bottom.\n')
	for face, tex in zip(faces_cap_bot, cap_bottom_texture_indices):
		f.write('f {0[0]}/{1[0]}/{2[0]} {0[1]}/{1[1]}/{2[1]} {0[2]}/{1[2]}/{2[2]}\n'.format(face, tex, bottom_cap_normal_indexes))


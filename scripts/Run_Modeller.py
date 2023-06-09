from modeller import *
from modeller.automodel import *
import os
from Bio import SeqIO
from scripts.Error import error_obj


data_list=[]
backup_lines=[]
def Prepare_MUT_Models(table_path,table_name,mut_pdb_path):
    if os.path.exists(mut_pdb_path) == False:
        os.mkdir(mut_pdb_path)
    with open(table_path+table_name,'r') as table:
        lines=table.readlines()
        for line in lines:
            backup_lines.append(line)
        if lines[0]!='id,wt_aa_short,mut_aa_short,loc,t_loc,wt_pdb_name,wt_pdb_path,mut_pdb_name,mut_pdb_path,wt_fasta_path,mut_fasta_path,wt_pssm_path,mut_pssm_path,wt_psi_blast_path,mut_psi_blast_path,wt_blastp_path,mut_blastp_path,pH,temperature,ddg\n':
            error_obj.Something_Wrong(Prepare_MUT_Models.__name__)
            exit(1)
        for line in lines[1:]:
            data_list.append(line.replace('\n',''))
    line_num=1
    for data in data_list:
        item_list=str(data).split(',')
        if len(item_list)!=20:
            error_obj.Something_Wrong(Prepare_MUT_Models.__name__)
            exit(1)
        fasta_path=item_list[10]
        template_pdb_path=item_list[6]
        pdb_name=item_list[7]
        files = os.listdir(mut_pdb_path)
        pdbs_names = []
        for file in files:
            pdbs_names.append(file.split('.')[0])
        if pdb_name in pdbs_names:
            item_list[8]=mut_pdb_path+pdb_name+'.pdb'
            if line_num!=len(backup_lines)-1:
                new_line=','.join(item_list)+'\n'
            else:
                new_line = ','.join(item_list)
            backup_lines[line_num]=new_line
            line_num+=1
            continue
        else:
            if not model_with_modeller(fasta_path, template_pdb_path, pdb_name, mut_pdb_path):
                error_obj.Modelling_Fail(Prepare_MUT_Models.__name__, pdb_name)
                return False
            item_list[8] = mut_pdb_path + pdb_name + '.pdb'
            if line_num!=len(backup_lines)-1:
                new_line=','.join(item_list)+'\n'
            else:
                new_line = ','.join(item_list)
            backup_lines[line_num]=new_line
            line_num+=1
    with open(table_path + table_name, 'w') as table:
        for line in backup_lines:
            table.write(line)
    return True








def model_with_modeller(fasta,pdb,name,path):
    query_seqres = SeqIO.parse(fasta, 'fasta')
    seq_dict = {}
    for chain in query_seqres:
        seq_dict[str(chain.id).split('_')[len(str(chain.id).split('_'))-1]]=str(chain.seq)
    with open('./'+name+'.ali','w') as ali:
        ali.write('>P1;' + name + '\n' + 'sequence:' + name + ':::::::0.00: 0.00\n')
        for id in seq_dict.keys():
            if id!=list(seq_dict.keys())[len(list(seq_dict.keys()))-1]:
                ali.write(seq_dict[id]+'/')
            else:
                ali.write(seq_dict[id]+'*')
    with open('./' + name + '.ali', 'r') as ali:
        print(ali.read())
    with open(pdb,'r') as f:
        with open('./temp.pdb','w') as p:
            p.write(f.read())
    #Alignment
    env1 = Environ()
    aln = Alignment(env1)
    print(list(seq_dict.keys()))
    mdl = Model(env1, file='./temp', model_segment=('FIRST:'+list(seq_dict.keys())[0], 'LAST:'+list(seq_dict.keys())[len(list(seq_dict.keys()))-1]))
    aln.append_model(mdl, align_codes=name + 'A', atom_files='./temp.pdb')
    aln.append(file='./'+name+'.ali', align_codes=name)
    aln.align2d(max_gap_length=50)
    aln.write(file='./'+name + '_out.ali', alignment_format='PIR')
    aln.write(file='./'+name + '_out.pap', alignment_format='PAP')

    #modelling
    env2 = Environ()
    a = AutoModel(env2, alnfile='./'+name + '_out.ali',
                  knowns=name + 'A', sequence=name,
                  assess_methods=(assess.DOPE,
                                  # soap_protein_od.Scorer(),
                                  assess.GA341))
    a.starting_model = 1
    a.ending_model = 3
    a.make()

    #Selecting
    lowest_molpdf = 1000000000
    pdb_res = ''
    for count in range(0, a.ending_model):
        if float(a.outputs[count]['molpdf']) < lowest_molpdf:
            lowest_molpdf = float(a.outputs[count]['molpdf'])
            pdb_res = a.outputs[count]['name']

    with open(pdb_res,'r') as p1:
        with open(path+name+'.pdb','w') as p2:
            p2.write(p1.read())

    #Clearing
    files_temp = os.listdir('./')
    for file in files_temp:
        file_div = file.split('.')
        if file_div[0] == name:
            os.remove(file)
        if file_div[0] == name + '_out':
            os.remove(file)
        if file == 'temp.pdb':
            os.remove(file)
    return True
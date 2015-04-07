type file;

app (file o) csv2nc(string ifile, string cdfile, string ofile) {
    csv2nc "-i" ifile "-d" cdfile "-o" ofile stdout = @o;
}

string infiles[]  = readData("/project/joshuaelliott/1896/src/crop_progress_county/csv2nc/in_files.txt");
string outfiles[] = readData("/project/joshuaelliott/1896/src/crop_progress_county/csv2nc/out_files.txt");
string cdfile     = "/project/joshuaelliott/1896/data/common/county_distances.csv";

foreach fin, idx in infiles {
   file fout <single_file_mapper; file = @strcat("./logs/out_", idx + 1, ".out")>;
   fout = csv2nc(fin, cdfile, outfiles[idx]);
}

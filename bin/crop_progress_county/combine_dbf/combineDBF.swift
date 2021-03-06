type file;

app (file o) combinedbf(string idir, string date, string dfile, string odir) {
    combinedbf "-i" idir "-d" date "-f" dfile "-o" odir stdout = @o;
}

string dates[] = readData("/project/joshuaelliott/1896/src/crop_progress_county/combine_dbf/uniq_dates.txt");
string indir   = "/project/joshuaelliott/1896/tmp/nc4.2009-2013";
string dimfile = "/project/joshuaelliott/1896/src/crop_progress_county/combine_dbf/var_county.nc4";
string outdir  = "/project/joshuaelliott/1896/tmp/nc4.2009-2013.combined";

foreach date in dates {
   file fout <single_file_mapper; file = @strcat("./logs/out_", date, ".out")>;
   fout = combinedbf(indir, date, dimfile, outdir);
}

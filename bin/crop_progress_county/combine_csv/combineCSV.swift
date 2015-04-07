type file;

app (file o) combinecsv(string idir, string date, string dfile, string odir) {
    combinecsv "-i" idir "-d" date "-f" dfile "-o" odir stdout = @o;
}

string dates[] = readData("/project/joshuaelliott/1896/src/crop_progress_county/combine_csv/uniq_dates.txt");
string indir   = "/project/joshuaelliott/1896/tmp/nc4.2014";
string dimfile = "/project/joshuaelliott/1896/src/crop_progress_county/combine_csv/var_county.nc4";
string outdir  = "/project/joshuaelliott/1896/tmp/nc4.2014.combined";

foreach date in dates {
   file fout <single_file_mapper; file = @strcat("./logs/out_", date, ".out")>;
   fout = combinecsv(indir, date, dimfile, outdir);
}



class TractCensusMerge {

    static def mergeBlockCensus(int[] a, int[] b ) {
        if (a.length != b.length) {
            println "Two lists length do not match!"
            exit(1)
        }
        for (int i = 0; i < a.length; i++)
            a[i] = a[i] + b[i]
        return a
    }


    static void main(String[] argv) {
        def tracts = new HashMap<String, HashMap<String, int[]>>()
        String dirPath = "../data/2010/"
        File p = new File(dirPath)
        String[] fnames = p.list()

        def cnt = 0
        fnames.each{ fn ->
            cnt++
            new File(dirPath + fn).withReader { reader ->
                String l = reader.readLine() // get rid of header
                while ((l = reader.readLine()) != null) {
                    String[] ls = l.split(",")
                    String org = ls[0].substring(0, ls[0].length() - 3)
                    String dst = ls[1].substring(0, ls[1].length() - 3)
                    int[] counts = new int[10]
                    for (int i = 0; i < 10; i++)
                        counts[i] = ls[i+2].toInteger()

                    if (tracts.containsKey(org))
                        if (tracts[org].containsKey(dst))
                            tracts[org][dst] = mergeBlockCensus(tracts[org][dst], counts)
                        else
                            tracts[org][dst] = counts
                    else {
                        tracts[org] = new HashMap<String, int[]>()
                        tracts[org][dst] = counts
                    }
                }
            }
            if (cnt % 5 == 0)
                println "$cnt out of ${fnames.length} files processed."
        }


        new File("../data/state_all_tract_level_od_JT00_2010").withWriter{ fout ->
            tracts.each{
                String org, HashMap<String, int[]> dict_dst ->
                    fout.write(org + ",")
                    dict_dst.each {
                        String dst, int[] counts ->
                            fout.write(dst)
                            counts.each { it ->
                                fout.write(",")
                                fout.write(it.toString())
                            }
                            fout.write("\n")
                }
            }
        }
    }
}

/*
 * GephiRun: headless Gephi Toolkit pipeline for the CSE3729 project networks.
 *
 * Uses Gephi's own engine (gephi-toolkit 0.11.4, the library behind Gephi Desktop 0.11.x):
 * graph store, statistics (Degree, Weighted Degree, Connected Components, Modularity, PageRank),
 * Giant Component filter, ForceAtlas2 layout, Preview renderer and PNG/SVG/PDF/GEXF exporters,
 * and the .gephi project format.
 *
 * Modes (run one per JVM via run.sh):
 *   type     (b) comment-kind -> reply-kind lift network, fixed two-column layout
 *   authors  (c) October author reply network, README sections 1, 2, 5, 6
 *   r4       (a) R4 cscq author-type network (outputs/15_network/network_profiled.gexf)
 *   conv     (d) conversation network components (no text labels)
 *   verify   re-open every projects/*.gephi and print node/edge counts per workspace
 *
 * Reproducibility: initial positions are drawn from java.util.Random(SEED) over nodes sorted by Id;
 * ForceAtlas2 runs with 1 thread and a fixed iteration count; Modularity runs with randomize = false.
 */

import java.awt.Color;
import java.awt.Font;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

import org.openide.util.Lookup;
import org.gephi.project.api.*;
import org.gephi.graph.api.*;
import org.gephi.statistics.plugin.*;
import org.gephi.filters.api.*;
import org.gephi.filters.plugin.graph.GiantComponentBuilder;
import org.gephi.layout.plugin.forceAtlas2.ForceAtlas2;
import org.gephi.layout.plugin.forceAtlas2.ForceAtlas2Builder;
import org.gephi.preview.api.*;
import org.gephi.preview.types.*;
import org.gephi.io.exporter.api.ExportController;
import org.gephi.io.exporter.preview.PDFExporter;
import org.gephi.io.exporter.plugin.ExporterGEXF;
import org.gephi.io.importer.api.*;
import org.gephi.io.processor.plugin.DefaultProcessor;

public class GephiRun {
    static final long SEED = 20261126L;
    static int THREADS = 1;
    static String[] ARGS;
    static File ARCH, FIG, STATS, PROJ;
    static PrintWriter LOG;

    static final Color[] TOP8 = {
        hex("#0072B2"), hex("#D55E00"), hex("#009E73"), hex("#CC79A7"),
        hex("#E69F00"), hex("#56B4E9"), hex("#882255"), hex("#999933")};
    static final Color GREY = hex("#C8C8C8");

    public static void main(String[] args) throws Exception {
        String mode = args[0];
        ARGS = args;
        ARCH = new File(args[1]);
        FIG = new File(ARCH, "gephi/figures"); FIG.mkdirs();
        STATS = new File(ARCH, "gephi/stats"); STATS.mkdirs();
        PROJ = new File(ARCH, "gephi/projects"); PROJ.mkdirs();
        LOG = new PrintWriter(new OutputStreamWriter(new FileOutputStream(new File(STATS, "run_" + mode + ".log")), StandardCharsets.UTF_8), true);
        log("mode=" + mode + " toolkit=0.11.4 java=" + System.getProperty("java.version") + " headless=" + java.awt.GraphicsEnvironment.isHeadless() + " seed=" + SEED);
        long t0 = System.currentTimeMillis();
        switch (mode) {
            case "type": runType(); break;
            case "authors": runAuthors(); break;
            case "r4": runR4(); break;
            case "conv": runConv(); break;
            case "relayout_authors": relayoutAuthors(); break;
            case "relayout_conv": relayoutConv(); break;
            case "recolor_authors": recolorAuthors(); break;
            case "layout_conv_full": layoutConvFull(); break;
            case "verify": runVerify(args.length > 2 && !args[2].isEmpty() ? args[2] : null); break;
            default: throw new IllegalArgumentException(mode);
        }
        log("done in " + (System.currentTimeMillis() - t0) / 1000 + " s");
        LOG.close();
        System.exit(0);
    }

    // ------------------------------------------------------------------ helpers
    static void log(String s) { System.out.println(s); if (LOG != null) LOG.println(s); }
    static Color hex(String h) { return Color.decode(h); }
    static <T> T lk(Class<T> c) { return Lookup.getDefault().lookup(c); }

    /** RFC4180 CSV reader (quoted fields, embedded commas, quotes and newlines). */
    static List<String[]> readCsv(File f) throws IOException {
        String s = new String(Files.readAllBytes(f.toPath()), StandardCharsets.UTF_8);
        if (s.startsWith("﻿")) s = s.substring(1);
        List<String[]> rows = new ArrayList<>();
        List<String> cur = new ArrayList<>();
        StringBuilder fld = new StringBuilder();
        boolean q = false;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (q) {
                if (c == '"') { if (i + 1 < s.length() && s.charAt(i + 1) == '"') { fld.append('"'); i++; } else q = false; }
                else fld.append(c);
            } else if (c == '"') q = true;
            else if (c == ',') { cur.add(fld.toString()); fld.setLength(0); }
            else if (c == '\n' || c == '\r') {
                if (c == '\r' && i + 1 < s.length() && s.charAt(i + 1) == '\n') i++;
                cur.add(fld.toString()); fld.setLength(0);
                rows.add(cur.toArray(new String[0])); cur.clear();
            } else fld.append(c);
        }
        if (fld.length() > 0 || !cur.isEmpty()) { cur.add(fld.toString()); rows.add(cur.toArray(new String[0])); }
        return rows;
    }

    static Map<String, Integer> hdr(String[] h) { Map<String, Integer> m = new HashMap<>(); for (int i = 0; i < h.length; i++) m.put(h[i], i); return m; }

    static String csvEsc(Object o) {
        if (o == null) return "";
        String s = o instanceof Double || o instanceof Float ? fmtNum(((Number) o).doubleValue()) : String.valueOf(o);
        if (s.contains(",") || s.contains("\"") || s.contains("\n") || s.contains("\r")) return "\"" + s.replace("\"", "\"\"") + "\"";
        return s;
    }
    static String fmtNum(double d) { if (d == Math.rint(d) && Math.abs(d) < 1e15) return String.valueOf((long) d); return String.valueOf(d); }

    /** Write a Gephi statistic report (HTML) and copy any chart images it references into stats/. */
    static void writeReport(String name, String html) throws IOException {
        Matcher m = Pattern.compile("(?i)src=\"(file:[^\"]+)\"").matcher(html);
        StringBuffer sb = new StringBuffer();
        int k = 0;
        while (m.find()) {
            String url = m.group(1);
            String dst = name + "_img" + (++k) + ".png";
            try {
                File src = new File(new java.net.URI(url));
                Files.copy(src.toPath(), new File(STATS, dst).toPath(), StandardCopyOption.REPLACE_EXISTING);
            } catch (Exception e) { log("  report image copy failed " + url + " : " + e); }
            m.appendReplacement(sb, Matcher.quoteReplacement("src=\"" + dst + "\""));
        }
        m.appendTail(sb);
        try (Writer w = new OutputStreamWriter(new FileOutputStream(new File(STATS, name + ".html")), StandardCharsets.UTF_8)) { w.write(sb.toString()); }
        log("  report -> stats/" + name + ".html (" + k + " images)");
    }

    static List<Column> exportable(Table t) {
        List<Column> cols = new ArrayList<>();
        for (Column c : t) {
            Class<?> tc = c.getTypeClass();
            if (Number.class.isAssignableFrom(tc) || tc == String.class || tc == Boolean.class || tc.isPrimitive()) cols.add(c);
        }
        return cols;
    }

    /** Data Laboratory style table export: every node column (Id, Label, originals, Gephi-computed). */
    static int exportNodes(Graph g, File f) throws IOException {
        Table t = g.getModel().getNodeTable();
        List<Column> cols = exportable(t);
        List<Node> nodes = new ArrayList<>(g.getNodes().toCollection());
        nodes.sort(Comparator.comparing(n -> String.valueOf(n.getId())));
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(f), StandardCharsets.UTF_8))) {
            StringJoiner h = new StringJoiner(",");
            for (Column c : cols) h.add(csvEsc(c.getTitle()));
            w.println(h);
            for (Node n : nodes) {
                StringJoiner r = new StringJoiner(",");
                for (Column c : cols) r.add(csvEsc(n.getAttribute(c)));
                w.println(r);
            }
        }
        log("  nodes table -> " + rel(f) + " rows=" + nodes.size());
        return nodes.size();
    }

    static int exportEdges(Graph g, File f) throws IOException {
        Table t = g.getModel().getEdgeTable();
        List<Column> cols = exportable(t);
        List<Edge> edges = new ArrayList<>(g.getEdges().toCollection());
        edges.sort(Comparator.comparing(e -> String.valueOf(e.getId())));
        try (PrintWriter w = new PrintWriter(new OutputStreamWriter(new FileOutputStream(f), StandardCharsets.UTF_8))) {
            StringJoiner h = new StringJoiner(",");
            h.add("Source").add("Target").add("Type");
            for (Column c : cols) h.add(csvEsc(c.getTitle()));
            w.println(h);
            for (Edge e : edges) {
                StringJoiner r = new StringJoiner(",");
                r.add(csvEsc(e.getSource().getId())).add(csvEsc(e.getTarget().getId())).add(e.isDirected() ? "Directed" : "Undirected");
                for (Column c : cols) r.add(csvEsc(e.getAttribute(c)));
                w.println(r);
            }
        }
        log("  edges table -> " + rel(f) + " rows=" + edges.size());
        return edges.size();
    }

    static Column byTitle(Table t, String title) {
        for (Column c : t) if (c.getTitle().equals(title) || c.getId().equals(title)) return c;
        throw new IllegalStateException("no column " + title);
    }

    static String rel(File f) { return ARCH.toPath().relativize(f.toPath()).toString(); }

    static double weightSum(Graph g) { double s = 0; for (Edge e : g.getEdges()) s += e.getWeight(); return s; }

    static void seedPositions(Graph g, double spread) {
        Random r = new Random(SEED);
        List<Node> nodes = new ArrayList<>(g.getNodes().toCollection());
        nodes.sort(Comparator.comparing(n -> String.valueOf(n.getId())));
        for (Node n : nodes) { n.setX((float) ((r.nextDouble() - 0.5) * spread)); n.setY((float) ((r.nextDouble() - 0.5) * spread)); }
    }

    static String fa2(GraphModel gm, int iters, double scaling, double gravity, boolean strongGravity, boolean linlog,
                      double ewi, int overlapIters) {
        ForceAtlas2 l = new ForceAtlas2Builder().buildLayout();
        l.setGraphModel(gm);
        l.resetPropertiesValues();
        l.setInitialisationSeed(SEED);
        l.setBarnesHutOptimize(true);
        l.setBarnesHutTheta(1.2);
        l.setThreadsCount(THREADS);
        l.setScalingRatio(scaling);
        l.setGravity(gravity);
        l.setStrongGravityMode(strongGravity);
        l.setLinLogMode(linlog);
        l.setEdgeWeightInfluence(ewi);
        l.setOutboundAttractionDistribution(false);
        l.setJitterTolerance(1.0);
        l.setAdjustSizes(false);
        l.initAlgo();
        for (int i = 0; i < iters && l.canAlgo(); i++) l.goAlgo();
        l.endAlgo();
        if (overlapIters > 0) {
            l.setAdjustSizes(true);
            l.initAlgo();
            for (int i = 0; i < overlapIters && l.canAlgo(); i++) l.goAlgo();
            l.endAlgo();
        }
        String s = String.format(Locale.ROOT, "ForceAtlas2(BarnesHut theta=1.2, threads=" + THREADS + ", scaling=%.1f, gravity=%.2f, strongGravity=%b, linLog=%b, edgeWeightInfluence=%.1f, dissuadeHubs=false, jitterTolerance=1.0) %d iterations, then preventOverlap(adjustSizes=true) %d iterations; initial positions java.util.Random(%d) over nodes sorted by Id",
                scaling, gravity, strongGravity, linlog, ewi, iters, overlapIters, SEED);
        log("  layout: " + s);
        return s;
    }

    static void basePreview(Workspace ws, float edgeOpacity, float edgeThickness, EdgeColor ec, boolean labels) {
        PreviewModel pm = lk(PreviewController.class).getModel(ws);
        PreviewProperties p = pm.getProperties();
        p.putValue(PreviewProperty.BACKGROUND_COLOR, Color.WHITE);
        p.putValue(PreviewProperty.SHOW_NODE_LABELS, labels);
        p.putValue(PreviewProperty.SHOW_EDGE_LABELS, false);
        p.putValue(PreviewProperty.EDGE_CURVED, false);
        p.putValue(PreviewProperty.EDGE_OPACITY, edgeOpacity);
        p.putValue(PreviewProperty.EDGE_THICKNESS, edgeThickness);
        p.putValue(PreviewProperty.EDGE_RESCALE_WEIGHT, false);
        p.putValue(PreviewProperty.EDGE_COLOR, ec);
        p.putValue(PreviewProperty.ARROW_SIZE, 0f);
        p.putValue(PreviewProperty.NODE_BORDER_WIDTH, 0f);
        p.putValue(PreviewProperty.NODE_OPACITY, 100f);
        p.putValue(PreviewProperty.MARGIN, 4f);
    }

    static void exportFigure(Workspace ws, String base, int w, int h, boolean vectors) throws IOException {
        PreviewController prc = lk(PreviewController.class);
        prc.refreshPreview(ws);
        ExportController ec = lk(ExportController.class);
        // Gephi's PNGExporter needs a screen device (G2DRenderTargetBuilder -> getDefaultScreenDevice) and throws
        // HeadlessException under -Djava.awt.headless=true. So the Preview is exported as PDF (and SVG) here, and
        // pdf_to_png.py rasterises the PDF to PNG at >= 3000 px wide. The drawing itself is Gephi's Preview render.
        PDFExporter pdf = (PDFExporter) ec.getExporter("pdf");
        pdf.setWorkspace(ws);
        pdf.setPageSize(new org.apache.pdfbox.pdmodel.common.PDRectangle(w / 4f, h / 4f));
        pdf.setLandscape(false);
        pdf.setMarginTop(8f); pdf.setMarginBottom(8f); pdf.setMarginLeft(8f); pdf.setMarginRight(8f);
        pdf.setTransparentBackground(false);
        ec.exportFile(new File(FIG, base + ".pdf"), pdf);
        log("  figure -> figures/" + base + ".pdf page " + (w / 4) + "x" + (h / 4) + " pt");
        if (vectors) {
            ec.exportFile(new File(FIG, base + ".svg"), ws);
            log("  figure -> figures/" + base + ".svg");
        }
    }

    static void exportGexf(Workspace ws, File f) throws IOException {
        ExportController ec = lk(ExportController.class);
        ExporterGEXF ex = (ExporterGEXF) ec.getExporter("gexf");
        ex.setWorkspace(ws);
        ex.setExportPosition(true); ex.setExportColors(true); ex.setExportSize(true); ex.setExportAttributes(true);
        ex.setExportVisible(false);
        ec.exportFile(f, ex);
        log("  gexf -> " + rel(f));
    }

    static void save(Project p, File f) {
        lk(ProjectController.class).saveProject(p, f);
        log("  project saved -> " + rel(f) + " (" + f.length() + " bytes)");
    }

    /** Size counts per Modularity class over graph g; returns map class->size, sorted by size desc then class. */
    static LinkedHashMap<Integer, Integer> classSizes(Graph g, String col) {
        Map<Integer, Integer> m = new HashMap<>();
        for (Node n : g.getNodes()) { Object v = n.getAttribute(col); if (v != null) m.merge(((Number) v).intValue(), 1, Integer::sum); }
        List<Map.Entry<Integer, Integer>> es = new ArrayList<>(m.entrySet());
        es.sort((a, b) -> b.getValue() != a.getValue().intValue() ? b.getValue() - a.getValue() : a.getKey() - b.getKey());
        LinkedHashMap<Integer, Integer> out = new LinkedHashMap<>();
        for (Map.Entry<Integer, Integer> e : es) out.put(e.getKey(), e.getValue());
        return out;
    }

    static void copyColumn(GraphModel gm, String from, String to, Class<?> type) {
        Table t = gm.getNodeTable();
        Column src = t.getColumn(from);
        Column dst = t.hasColumn(to) ? t.getColumn(to) : t.addColumn(to, type);
        for (Node n : gm.getGraph().getNodes()) n.setAttribute(dst, n.getAttribute(src));
    }

    static Map<String, String> runModularity(GraphModel gm, double res, String tag, String reportName, PrintWriter summary, int topK) throws IOException {
        Modularity mod = new Modularity();
        mod.setUseWeight(true);
        mod.setResolution(res);
        mod.setRandom(false);
        mod.execute(gm);
        Graph g = gm.getGraphVisible();
        LinkedHashMap<Integer, Integer> sizes = classSizes(g, Modularity.MODULARITY_CLASS);
        int n = g.getNodeCount();
        StringBuilder top = new StringBuilder();
        int k = 0;
        for (Map.Entry<Integer, Integer> e : sizes.entrySet()) {
            if (k++ >= topK) break;
            top.append(String.format(Locale.ROOT, "%sclass %d: %d (%.2f%%)", k > 1 ? "; " : "", e.getKey(), e.getValue(), 100.0 * e.getValue() / n));
        }
        log(String.format(Locale.ROOT, "  Modularity %s: resolution=%.1f useWeight=true randomize=false Q=%.4f classes=%d visibleNodes=%d visibleEdges=%d top: %s",
                tag, res, mod.getModularity(), sizes.size(), n, g.getEdgeCount(), top));
        if (summary != null) {
            summary.printf(Locale.ROOT, "%s,%.1f,true,false,%.6f,%d,%d,%d,\"%s\"%n", tag, res, mod.getModularity(), sizes.size(), n, g.getEdgeCount(), top);
        }
        writeReport(reportName, mod.getReport());
        Map<String, String> r = new HashMap<>();
        r.put("Q", String.format(Locale.ROOT, "%.4f", mod.getModularity()));
        r.put("classes", String.valueOf(sizes.size()));
        return r;
    }

    // ------------------------------------------------------------------ (b) type network
    static void runType() throws Exception {
        ProjectController pc = lk(ProjectController.class);
        pc.newProject();
        Project project = pc.getCurrentProject();
        Workspace ws = pc.getCurrentWorkspace();
        pc.renameWorkspace(ws, "Comment kind to reply kind (lift)");
        GraphModel gm = lk(GraphController.class).getGraphModel(ws);
        Table nt = gm.getNodeTable(), et = gm.getEdgeTable();
        Column side = nt.addColumn("side", String.class);
        Column pct = et.addColumn("pct", Double.class);
        Column replies = et.addColumn("replies", Integer.class);
        Column band = et.addColumn("lift_band", String.class);
        DirectedGraph g = gm.getDirectedGraph();
        GraphFactory f = gm.factory();
        File dir = new File(ARCH, "outputs/12_replies/gephi");
        List<String[]> nr = readCsv(new File(dir, "type_nodes.csv"));
        Map<String, Integer> nh = hdr(nr.get(0));
        int li = 0, ri = 0;
        int nLeft = 0, nRight = 0;
        for (int i = 1; i < nr.size(); i++) if (nr.get(i)[nh.get("side")].equals("comment")) nLeft++; else nRight++;
        double leftGap = 110, rightGap = leftGap * (nLeft - 1) / (nRight - 1);
        for (int i = 1; i < nr.size(); i++) {
            String[] r = nr.get(i);
            Node n = f.newNode(r[nh.get("Id")]);
            boolean left = r[nh.get("side")].equals("comment");
            String lab = r[nh.get("Label")];
            n.setLabel(left ? lab.replace("_", " ") : lab);
            n.setAttribute(side, r[nh.get("side")]);
            if (left) { n.setX(-520f); n.setY((float) (leftGap * (nLeft - 1) / 2.0 - leftGap * li++)); n.setColor(hex("#4D4D4D")); }
            else { n.setX(520f); n.setY((float) (rightGap * (nRight - 1) / 2.0 - rightGap * ri++)); n.setColor(hex("#009E73")); }
            n.setSize(22f);
            g.addNode(n);
        }
        List<String[]> er = readCsv(new File(dir, "type_edges.csv"));
        Map<String, Integer> eh = hdr(er.get(0));
        int k = 0;
        for (int i = 1; i < er.size(); i++) {
            String[] r = er.get(i);
            double w = Double.parseDouble(r[eh.get("Weight")]);
            Edge e = f.newEdge("e" + (k++), g.getNode(r[eh.get("Source")]), g.getNode(r[eh.get("Target")]), 0, w, true);
            e.setAttribute(pct, Double.parseDouble(r[eh.get("pct")]));
            e.setAttribute(replies, Integer.parseInt(r[eh.get("replies")]));
            String b; Color c;
            if (w >= 1.2) { b = ">=1.2"; c = hex("#D55E00"); }
            else if (w >= 1.0) { b = "1.0-1.2"; c = hex("#8C8C8C"); }
            else { b = "<1.0"; c = hex("#DADADA"); }
            e.setAttribute(band, b);
            e.setColor(c);
            g.addEdge(e);
        }
        log("type network: nodes=" + g.getNodeCount() + " edges=" + g.getEdgeCount());
        Degree d = new Degree(); d.execute(gm); writeReport("type_degree_report", d.getReport());
        WeightedDegree wd = new WeightedDegree(); wd.execute(gm); writeReport("type_weighted_degree_report", wd.getReport());
        exportNodes(g, new File(STATS, "type_network_nodes.csv"));
        exportEdges(g, new File(STATS, "type_network_edges.csv"));

        basePreview(ws, 100f, 7f, new EdgeColor(EdgeColor.Mode.ORIGINAL), true);
        PreviewProperties p = lk(PreviewController.class).getModel(ws).getProperties();
        p.putValue(PreviewProperty.NODE_LABEL_FONT, new Font("SansSerif", Font.BOLD, 24));
        p.putValue(PreviewProperty.NODE_LABEL_PROPORTIONAL_SIZE, false);
        p.putValue(PreviewProperty.NODE_LABEL_COLOR, new DependantOriginalColor(Color.BLACK));
        p.putValue(PreviewProperty.NODE_LABEL_OUTLINE_SIZE, 6f);
        p.putValue(PreviewProperty.NODE_LABEL_OUTLINE_COLOR, new DependantColor(Color.WHITE));
        p.putValue(PreviewProperty.NODE_LABEL_OUTLINE_OPACITY, 90f);
        p.putValue(PreviewProperty.NODE_LABEL_AVOID_OVERLAP, false);
        p.putValue(PreviewProperty.NODE_LABEL_SHORTEN, false);
        p.putValue(PreviewProperty.MARGIN, 12f);
        exportFigure(ws, "type_network_lift", 3600, 3000, true);
        exportGexf(ws, new File(PROJ, "type_network_lift.gexf"));
        save(project, new File(PROJ, "type_network_lift.gephi"));
    }

    // ------------------------------------------------------------------ (c) authors network
    static DirectedGraph buildAuthors(GraphModel gm, Set<String> keep) throws IOException {
        Table nt = gm.getNodeTable(), et = gm.getEdgeTable();
        String[] ncols = {"ScopeCommentCount", "OutDegreeRetained", "InDegreeRetained", "OutWeightRetained", "InWeightRetained"};
        for (String c : ncols) if (!nt.hasColumn(c)) nt.addColumn(c, Integer.class);
        if (!et.hasColumn("ThreadCount")) { et.addColumn("ThreadCount", Integer.class); et.addColumn("FirstReplyUTC", String.class); et.addColumn("LastReplyUTC", String.class); }
        DirectedGraph g = gm.getDirectedGraph();
        GraphFactory f = gm.factory();
        File dir = new File(ARCH, "gephi/exports/authors_keyword-comments_direct");
        List<String[]> nr = readCsv(new File(dir, "nodes.csv"));
        Map<String, Integer> nh = hdr(nr.get(0));
        for (int i = 1; i < nr.size(); i++) {
            String[] r = nr.get(i);
            String id = r[nh.get("Id")];
            if (keep != null && !keep.contains(id)) continue;
            Node n = f.newNode(id);
            n.setLabel(r[nh.get("Label")]);
            for (String c : ncols) n.setAttribute(c, Integer.parseInt(r[nh.get(c)]));
            g.addNode(n);
        }
        List<String[]> er = readCsv(new File(dir, "edges.csv"));
        Map<String, Integer> eh = hdr(er.get(0));
        for (int i = 1; i < er.size(); i++) {
            String[] r = er.get(i);
            Node s = g.getNode(r[eh.get("Source")]), t = g.getNode(r[eh.get("Target")]);
            if (s == null || t == null) { if (keep == null) throw new IllegalStateException("missing endpoint " + Arrays.toString(r)); continue; }
            Edge e = f.newEdge(r[eh.get("Id")], s, t, 0, Double.parseDouble(r[eh.get("Weight")]), true);
            e.setAttribute("ThreadCount", Integer.parseInt(r[eh.get("ThreadCount")]));
            e.setAttribute("FirstReplyUTC", r[eh.get("FirstReplyUTC")]);
            e.setAttribute("LastReplyUTC", r[eh.get("LastReplyUTC")]);
            g.addEdge(e);
        }
        return g;
    }

    static void runAuthors() throws Exception {
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        pc.newProject();
        Project project = pc.getCurrentProject();
        Workspace ws1 = pc.getCurrentWorkspace();
        pc.renameWorkspace(ws1, "Full network (14,507 users)");
        GraphModel gm1 = gc.getGraphModel(ws1);
        DirectedGraph g1 = buildAuthors(gm1, null);
        log(String.format(Locale.ROOT, "authors full: nodes=%d edges=%d weightSum=%s directed=%b", g1.getNodeCount(), g1.getEdgeCount(), fmtNum(weightSum(g1)), gm1.isDirected()));
        Degree d = new Degree(); d.execute(gm1);
        log(String.format(Locale.ROOT, "  Average Degree (Gephi, directed report) = %.4f", d.getAverageDegree()));
        writeReport("authors_full_average_degree_report", d.getReport());
        WeightedDegree wd = new WeightedDegree(); wd.execute(gm1);
        log(String.format(Locale.ROOT, "  Average Weighted Degree (Gephi) = %.4f", wd.getAverageDegree()));
        writeReport("authors_full_weighted_degree_report", wd.getReport());
        ConnectedComponents cc = new ConnectedComponents(); cc.setDirected(true); cc.execute(gm1);
        int[] cs = cc.getComponentsSize();
        int max = 0, two = 0; for (int s : cs) { max = Math.max(max, s); if (s == 2) two++; }
        log(String.format(Locale.ROOT, "  Connected Components: weak=%d largest=%d (%.2f%%) twoUserComponents=%d", cc.getConnectedComponentsCount(), max, 100.0 * max / g1.getNodeCount(), two));
        writeReport("authors_full_connected_components_report", cc.getReport());
        // Full-network layout so the first workspace is readable when opened in Desktop.
        seedPositions(g1, 2000);
        for (Node n : g1.getNodes()) { n.setSize(4f + 0.15f * ((Integer) n.getAttribute("InWeightRetained"))); n.setColor(hex("#7F7F7F")); }
        THREADS = 4;
        layoutFullAuthors(gm1);
        int nf = exportNodes(g1, new File(STATS, "nodes_full_metrics.csv"));
        int ef = exportEdges(g1, new File(STATS, "edges_full.csv"));

        // Giant Component filter (Topology > Giant Component), as README section 5.
        FilterController fc = lk(FilterController.class);
        GiantComponentBuilder.GiantComponentFilter gcf = new GiantComponentBuilder.GiantComponentFilter();
        gcf.init(gm1.getGraph());
        Query q = fc.createQuery(gcf);
        GraphView view = fc.filter(q);
        gm1.setVisibleView(view);
        Graph vis = gm1.getGraphVisible();
        Set<String> keep = new HashSet<>();
        for (Node n : vis.getNodes()) keep.add((String) n.getId());
        log(String.format(Locale.ROOT, "  Giant Component filter: visible nodes=%d visible edges=%d", vis.getNodeCount(), vis.getEdgeCount()));
        gm1.setVisibleView(null);
        fc.remove(q);

        // Materialise the filtered view as its own workspace so the saved project opens on it directly.
        Workspace ws2 = pc.newWorkspace(project);
        pc.renameWorkspace(ws2, "Largest weak component (9,330 users)");
        pc.openWorkspace(ws2);
        GraphModel gm2 = gc.getGraphModel(ws2);
        DirectedGraph g2 = buildAuthors(gm2, keep);
        log(String.format(Locale.ROOT, "authors LWCC workspace: nodes=%d edges=%d weightSum=%s", g2.getNodeCount(), g2.getEdgeCount(), fmtNum(weightSum(g2))));
        Degree d2 = new Degree(); d2.execute(gm2);
        WeightedDegree wd2 = new WeightedDegree(); wd2.execute(gm2);
        ConnectedComponents cc2 = new ConnectedComponents(); cc2.setDirected(true); cc2.execute(gm2);
        log("  LWCC check: weak components=" + cc2.getConnectedComponentsCount());

        File sumF = new File(STATS, "authors_modularity_runs.csv");
        try (PrintWriter sum = new PrintWriter(new OutputStreamWriter(new FileOutputStream(sumF), StandardCharsets.UTF_8))) {
            sum.println("run,resolution,use_weight,randomize,Q_gephi,classes,visible_nodes,visible_edges,top5");
            runModularity(gm2, 0.5, "r050", "authors_lwcc_modularity_r050_report", sum, 5);
            copyColumn(gm2, Modularity.MODULARITY_CLASS, "modularity_class_r050", Integer.class);
            exportNodes(g2, new File(STATS, "nodes_largest_component_modularity_r050.csv"));
            runModularity(gm2, 1.5, "r150", "authors_lwcc_modularity_r150_report", sum, 5);
            copyColumn(gm2, Modularity.MODULARITY_CLASS, "modularity_class_r150", Integer.class);
            exportNodes(g2, new File(STATS, "nodes_largest_component_modularity_r150.csv"));
            runModularity(gm2, 1.0, "r100_baseline", "authors_lwcc_modularity_r1_report", sum, 5);
        }
        int nl = exportNodes(g2, new File(STATS, "nodes_largest_component_modularity_r1.csv"));
        exportEdges(g2, new File(STATS, "edges_largest_component.csv"));
        // group sizes for baseline
        LinkedHashMap<Integer, Integer> sizes = classSizes(g2, Modularity.MODULARITY_CLASS);
        try (PrintWriter w = new PrintWriter(new File(STATS, "authors_lwcc_modularity_r1_group_sizes.csv"), "UTF-8")) {
            w.println("rank,modularity_class,users,share_of_lwcc_pct");
            int r = 0; for (Map.Entry<Integer, Integer> e : sizes.entrySet()) w.printf(Locale.ROOT, "%d,%d,%d,%.2f%n", ++r, e.getKey(), e.getValue(), 100.0 * e.getValue() / g2.getNodeCount());
        }
        // Appearance: colour = modularity class (top 8 fixed palette, other classes grey), size = InWeightRetained 5-30.
        Map<Integer, Color> col = new HashMap<>();
        int r = 0;
        for (Integer c : sizes.keySet()) {
            Color cl = r < 8 ? TOP8[r] : GREY;
            col.put(c, cl); r++;
        }
        int mn = Integer.MAX_VALUE, mx = Integer.MIN_VALUE;
        for (Node n : g2.getNodes()) { int v = (Integer) n.getAttribute("InWeightRetained"); mn = Math.min(mn, v); mx = Math.max(mx, v); }
        for (Node n : g2.getNodes()) {
            int v = (Integer) n.getAttribute("InWeightRetained");
            n.setSize((float) (5 + 25.0 * (v - mn) / Math.max(1, mx - mn)));
            n.setColor(col.get(((Number) n.getAttribute(Modularity.MODULARITY_CLASS)).intValue()));
        }
        log("  size ranking InWeightRetained min=" + mn + " max=" + mx + " -> 5..30");
        try (PrintWriter w = new PrintWriter(new File(STATS, "authors_lwcc_palette.csv"), "UTF-8")) {
            w.println("rank,modularity_class,users,hex");
            int k = 0; for (Map.Entry<Integer, Integer> e : sizes.entrySet()) { Color c = col.get(e.getKey()); w.printf("%d,%d,%d,#%02X%02X%02X%n", ++k, e.getKey(), e.getValue(), c.getRed(), c.getGreen(), c.getBlue()); }
        }
        // Final settings (README's scaling 100 left nodes invisible at slide size; see analysis_notes.md section 3).
        seedPositions(g2, 3000);
        String lay = fa2(gm2, 1500, 10, 1.0, true, false, 1.0, 200);
        try (PrintWriter w = new PrintWriter(new File(STATS, "authors_layout_settings.txt"), "UTF-8")) { w.println(lay); w.println(LWCC_STYLE); }
        colourFullFromLwcc(g1, g2);
        basePreview(ws1, 30f, 1.0f, new EdgeColor(EdgeColor.Mode.MIXED), false);
        basePreview(ws2, 45f, 1.5f, new EdgeColor(EdgeColor.Mode.MIXED), false);
        exportFigure(ws2, "largest_component_communities", 4000, 4000, true);
        exportGexf(ws2, new File(PROJ, "author_replies_largest_component.gexf"));
        pc.openWorkspace(ws2);
        save(project, new File(PROJ, "author_replies.gephi"));
        log(String.format("CHECK nodes_full_metrics rows=%d edges_full rows=%d lwcc rows=%d", nf, ef, nl));
    }

    // ------------------------------------------------------------------ (a) R4 cscq author types
    static void runR4() throws Exception {
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        pc.newProject();
        Project project = pc.getCurrentProject();
        Workspace ws = pc.getCurrentWorkspace();
        pc.renameWorkspace(ws, "R4 author types (colour = type)");
        ImportController ic = lk(ImportController.class);
        Container c = ic.importFile(new File(ARCH, "outputs/15_network/network_profiled.gexf"));
        c.getLoader().setEdgeDefault(EdgeDirectionDefault.DIRECTED);
        ic.process(c, new DefaultProcessor(), ws);
        GraphModel gm = gc.getGraphModel(ws);
        Graph g = gm.getGraph();
        log(String.format(Locale.ROOT, "r4: nodes=%d edges=%d weightSum=%s directed=%b", g.getNodeCount(), g.getEdgeCount(), fmtNum(weightSum(g)), gm.isDirected()));
        Degree d = new Degree(); d.execute(gm); writeReport("r4_degree_report", d.getReport());
        log(String.format(Locale.ROOT, "  Average Degree = %.4f", d.getAverageDegree()));
        WeightedDegree wd = new WeightedDegree(); wd.execute(gm); writeReport("r4_weighted_degree_report", wd.getReport());
        log(String.format(Locale.ROOT, "  Average Weighted Degree = %.4f", wd.getAverageDegree()));
        ConnectedComponents cc = new ConnectedComponents(); cc.setDirected(true); cc.execute(gm);
        int[] cs = cc.getComponentsSize(); int max = 0; for (int s : cs) max = Math.max(max, s);
        log(String.format(Locale.ROOT, "  Connected Components: weak=%d largest=%d (%.2f%%)", cc.getConnectedComponentsCount(), max, 100.0 * max / g.getNodeCount()));
        writeReport("r4_connected_components_report", cc.getReport());
        try (PrintWriter sum = new PrintWriter(new OutputStreamWriter(new FileOutputStream(new File(STATS, "r4_modularity_runs.csv")), StandardCharsets.UTF_8))) {
            sum.println("run,resolution,use_weight,randomize,Q_gephi,classes,visible_nodes,visible_edges,top8");
            runModularity(gm, 1.0, "r100", "r4_modularity_report", sum, 8);
        }
        PageRank pr = new PageRank(); pr.setDirected(true); pr.setProbability(0.85); pr.setEpsilon(0.001); pr.setUseEdgeWeight(true);
        pr.execute(gm); writeReport("r4_pagerank_report", pr.getReport());
        log("  PageRank directed=true p=0.85 eps=0.001 useEdgeWeight=true");

        Map<String, Color> typeCol = new HashMap<>();
        typeCol.put("story-sharer", hex("#0072B2")); typeCol.put("blame-talker", hex("#D55E00"));
        typeCol.put("helper", hex("#009E73")); typeCol.put("other", hex("#CC79A7")); typeCol.put("low-activity", hex("#BBBBBB"));
        Column typeC = byTitle(gm.getNodeTable(), "type");
        Column prC = gm.getNodeTable().getColumn(PageRank.PAGERANK);
        double pmin = Double.MAX_VALUE, pmax = 0;
        for (Node n : g.getNodes()) { double v = (Double) n.getAttribute(prC); pmin = Math.min(pmin, v); pmax = Math.max(pmax, v); }
        Map<String, Integer> typeCounts = new TreeMap<>();
        for (Node n : g.getNodes()) {
            double v = (Double) n.getAttribute(prC);
            // Gephi Ranking (linear) on PageRank, size 4..40; sqrt transform so the long tail stays visible
            double t = Math.sqrt((v - pmin) / (pmax - pmin));
            n.setSize((float) (4 + 36 * t));
            String ty = String.valueOf(n.getAttribute(typeC));
            typeCounts.merge(ty, 1, Integer::sum);
            n.setColor(typeCol.getOrDefault(ty, GREY));
        }
        log("  type counts " + typeCounts + " pagerank min=" + pmin + " max=" + pmax);
        seedPositions(g, 3000);
        // Strong gravity keeps the 48 tiny components next to the giant one (otherwise they fly off and the
        // giant component renders as a dot). 4 threads: near-identical but not bit-identical between runs.
        THREADS = 4;
        String lay = fa2(gm, 1000, 10, 1.0, true, false, 1.0, 100);
        try (PrintWriter w = new PrintWriter(new File(STATS, "r4_layout_settings.txt"), "UTF-8")) { w.println(lay); w.println("size = 4 + 36*sqrt((pagerank-min)/(max-min))"); }
        exportNodes(g, new File(STATS, "r4_nodes_gephi_metrics.csv"));
        exportEdges(g, new File(STATS, "r4_edges.csv"));
        basePreview(ws, 6f, 0.6f, new EdgeColor(EdgeColor.Mode.SOURCE), false);
        exportFigure(ws, "r4_author_types", 4000, 4000, false);
        exportGexf(ws, new File(PROJ, "r4_cscq_author_types.gexf"));

        // Second workspace: same positions, colour = Gephi Modularity class (8 largest coloured, rest grey).
        Workspace ws2 = pc.duplicateWorkspace(ws);
        pc.renameWorkspace(ws2, "R4 Gephi modularity (8 largest coloured)");
        pc.openWorkspace(ws2);
        GraphModel gm2 = gc.getGraphModel(ws2);
        Graph g2 = gm2.getGraph();
        log("  duplicated workspace nodes=" + g2.getNodeCount() + " edges=" + g2.getEdgeCount());
        LinkedHashMap<Integer, Integer> sizes = classSizes(g2, Modularity.MODULARITY_CLASS);
        Map<Integer, Color> col = new HashMap<>(); int r = 0;
        try (PrintWriter w = new PrintWriter(new File(STATS, "r4_modularity_group_sizes.csv"), "UTF-8")) {
            w.println("rank,modularity_class,users,share_pct,hex");
            for (Map.Entry<Integer, Integer> e : sizes.entrySet()) {
                Color cl = r < 8 ? TOP8[r] : GREY; col.put(e.getKey(), cl); r++;
                w.printf(Locale.ROOT, "%d,%d,%d,%.2f,#%02X%02X%02X%n", r, e.getKey(), e.getValue(), 100.0 * e.getValue() / g2.getNodeCount(), cl.getRed(), cl.getGreen(), cl.getBlue());
            }
        }
        for (Node n : g2.getNodes()) n.setColor(col.get(((Number) n.getAttribute(Modularity.MODULARITY_CLASS)).intValue()));
        basePreview(ws2, 6f, 0.6f, new EdgeColor(EdgeColor.Mode.SOURCE), false);
        exportFigure(ws2, "r4_modularity", 4000, 4000, false);
        // Type x modularity crosstab (for the notes)
        Map<String, Integer> ct = new TreeMap<>();
        for (Node n : g2.getNodes()) {
            int cls = ((Number) n.getAttribute(Modularity.MODULARITY_CLASS)).intValue();
            ct.merge(cls + "|" + n.getAttribute(byTitle(gm2.getNodeTable(), "type")), 1, Integer::sum);
        }
        try (PrintWriter w = new PrintWriter(new File(STATS, "r4_type_by_modularity_class.csv"), "UTF-8")) {
            w.println("modularity_class,type,users");
            for (Map.Entry<String, Integer> e : ct.entrySet()) { String[] p = e.getKey().split("\\|"); w.println(p[0] + "," + p[1] + "," + e.getValue()); }
        }
        pc.openWorkspace(ws);
        save(project, new File(PROJ, "r4_cscq_author_types.gephi"));
    }

    // ------------------------------------------------------------------ (d) conversation network
    static void runConv() throws Exception {
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        pc.newProject();
        Project project = pc.getCurrentProject();
        Workspace ws = pc.getCurrentWorkspace();
        pc.renameWorkspace(ws, "Conversation network (posts and comments)");
        GraphModel gm = gc.getGraphModel(ws);
        Table nt = gm.getNodeTable(), et = gm.getEdgeTable();
        File dir = new File(ARCH, "gephi/exports/conversations_keyword-posts_direct");
        List<String[]> nr = readCsv(new File(dir, "nodes.csv"));
        String[] nhd = nr.get(0);
        Map<String, Integer> nh = hdr(nhd);
        // TextPreview is deliberately not imported (no text is rendered or stored in the project).
        List<String> keepCols = new ArrayList<>();
        for (String h : nhd) if (!h.equals("Id") && !h.equals("Label") && !h.equals("TextPreview")) { keepCols.add(h); nt.addColumn(h, String.class); }
        DirectedGraph g = gm.getDirectedGraph();
        GraphFactory f = gm.factory();
        for (int i = 1; i < nr.size(); i++) {
            String[] r = nr.get(i);
            Node n = f.newNode(r[nh.get("Id")]);
            n.setLabel(r[nh.get("Label")]);
            for (String c : keepCols) n.setAttribute(c, r[nh.get(c)]);
            g.addNode(n);
        }
        List<String[]> er = readCsv(new File(dir, "edges.csv"));
        String[] ehd = er.get(0);
        Map<String, Integer> eh = hdr(ehd);
        List<String> ecols = new ArrayList<>();
        for (String h : ehd) if (!Arrays.asList("Id", "Source", "Target", "Type", "Weight").contains(h)) { ecols.add(h); et.addColumn(h, String.class); }
        int missing = 0;
        for (int i = 1; i < er.size(); i++) {
            String[] r = er.get(i);
            Node s = g.getNode(r[eh.get("Source")]), t = g.getNode(r[eh.get("Target")]);
            if (s == null || t == null) { missing++; continue; }
            Edge e = f.newEdge(r[eh.get("Id")], s, t, 0, Double.parseDouble(r[eh.get("Weight")]), true);
            for (String c : ecols) e.setAttribute(c, r[eh.get(c)]);
            g.addEdge(e);
        }
        log(String.format(Locale.ROOT, "conv: nodes=%d edges=%d missingEndpointEdges=%d", g.getNodeCount(), g.getEdgeCount(), missing));
        Degree d = new Degree(); d.execute(gm); writeReport("conv_degree_report", d.getReport());
        log(String.format(Locale.ROOT, "  Average Degree = %.4f", d.getAverageDegree()));
        ConnectedComponents cc = new ConnectedComponents(); cc.setDirected(true); cc.execute(gm);
        int[] cs = cc.getComponentsSize().clone(); Arrays.sort(cs);
        int max = cs[cs.length - 1];
        log(String.format(Locale.ROOT, "  Connected Components: weak=%d largest=%d (%.2f%%) top10=%s", cc.getConnectedComponentsCount(), max, 100.0 * max / g.getNodeCount(),
                Arrays.toString(Arrays.copyOfRange(cs, Math.max(0, cs.length - 10), cs.length))));
        writeReport("conv_connected_components_report", cc.getReport());
        int maxIn = 0; for (Node n : g.getNodes()) maxIn = Math.max(maxIn, g.getInDegree(n));
        Map<String, Color> sub = new HashMap<>();
        sub.put("cscareerquestions", hex("#E69F00")); sub.put("technology", hex("#56B4E9")); sub.put("programming", hex("#009E73"));
        Map<String, Integer> subCounts = new TreeMap<>();
        for (Node n : g.getNodes()) {
            String s = String.valueOf(n.getAttribute("Subreddit"));
            subCounts.merge(s, 1, Integer::sum);
            n.setColor(sub.getOrDefault(s, GREY));
            n.setSize((float) (3 + 27 * Math.sqrt(g.getInDegree(n) / (double) Math.max(1, maxIn))));
        }
        log("  subreddit counts " + subCounts + " maxInDegree=" + maxIn);
        exportNodes(g, new File(STATS, "conv_nodes_gephi_metrics.csv"));
        // Figure: the 30 largest weak components only (filter by component id), labels off.
        Column comp = nt.getColumn(ConnectedComponents.WEAKLY);
        Map<Integer, Integer> csz = new HashMap<>();
        for (Node n : g.getNodes()) csz.merge(((Number) n.getAttribute(comp)).intValue(), 1, Integer::sum);
        List<Map.Entry<Integer, Integer>> es = new ArrayList<>(csz.entrySet());
        es.sort((a, b) -> b.getValue() - a.getValue());
        Set<Integer> top = new HashSet<>();
        for (int i = 0; i < Math.min(30, es.size()); i++) top.add(es.get(i).getKey());
        Workspace ws2 = pc.duplicateWorkspace(ws);
        pc.renameWorkspace(ws2, "30 largest components (figure)");
        pc.openWorkspace(ws2);
        GraphModel gm2 = gc.getGraphModel(ws2);
        Graph g2 = gm2.getGraph();
        List<Node> drop = new ArrayList<>();
        Column comp2 = gm2.getNodeTable().getColumn(ConnectedComponents.WEAKLY);
        for (Node n : g2.getNodes()) if (!top.contains(((Number) n.getAttribute(comp2)).intValue())) drop.add(n);
        g2.removeAllNodes(drop);
        log("  figure workspace (30 largest components): nodes=" + g2.getNodeCount() + " edges=" + g2.getEdgeCount());
        THREADS = 4;
        seedPositions(g2, 3000);
        String lay = fa2(gm2, 2000, 1, 8.0, false, false, 1.0, 200);
        try (PrintWriter w = new PrintWriter(new File(STATS, "conv_layout_settings.txt"), "UTF-8")) { w.println(lay); w.println("size = 3 + 27*sqrt(indegree/maxIndegree); colour = Subreddit; 30 largest weak components; labels off (TextPreview never imported)"); }
        basePreview(ws2, 60f, 1.5f, new EdgeColor(EdgeColor.Mode.SOURCE), false);
        exportFigure(ws2, "conversation_largest_components", 4000, 4000, true);
        layoutConvWs0(gm, ws);
        pc.openWorkspace(ws2);
        save(project, new File(PROJ, "conversations.gephi"));
    }

    // ------------------------------------------------------------------ re-layout the saved LWCC workspace
    /** args: relayout_authors ARCH scaling gravity strongGravity iters overlapIters threads [linLog] */
    static void relayoutAuthors() throws Exception {
        double scaling = Double.parseDouble(ARGS[2]), gravity = Double.parseDouble(ARGS[3]);
        boolean strong = Boolean.parseBoolean(ARGS[4]);
        int iters = Integer.parseInt(ARGS[5]), ov = Integer.parseInt(ARGS[6]);
        THREADS = Integer.parseInt(ARGS[7]);
        boolean linlog = ARGS.length > 8 && Boolean.parseBoolean(ARGS[8]);
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        File pf = new File(PROJ, "author_replies.gephi");
        Project p = pc.openProject(pf);
        Workspace target = null;
        for (Workspace w : p.getLookup().lookup(WorkspaceProvider.class).getWorkspaces()) {
            WorkspaceInformation info = w.getLookup().lookup(WorkspaceInformation.class);
            if (info != null && info.getName().startsWith("Largest")) target = w;
        }
        pc.openWorkspace(target);
        GraphModel gm = gc.getGraphModel(target);
        Graph g = gm.getGraph();
        log("relayout LWCC: nodes=" + g.getNodeCount() + " edges=" + g.getEdgeCount());
        seedPositions(g, 3000);
        String lay = fa2(gm, iters, scaling, gravity, strong, linlog, 1.0, ov);
        try (PrintWriter w = new PrintWriter(new File(STATS, "authors_layout_settings.txt"), "UTF-8")) { w.println(lay); w.println(LWCC_STYLE); }
        float minx = Float.MAX_VALUE, maxx = -Float.MAX_VALUE;
        for (Node n : g.getNodes()) { minx = Math.min(minx, n.x()); maxx = Math.max(maxx, n.x()); }
        log("  x extent " + minx + " .. " + maxx);
        basePreview(target, 45f, 1.5f, new EdgeColor(EdgeColor.Mode.MIXED), false);
        exportFigure(target, "largest_component_communities", 4000, 4000, true);
        exportGexf(target, new File(PROJ, "author_replies_largest_component.gexf"));
        save(p, pf);
    }

    /** args: relayout_conv ARCH scaling gravity strongGravity iters overlapIters threads */
    static void relayoutConv() throws Exception {
        double scaling = Double.parseDouble(ARGS[2]), gravity = Double.parseDouble(ARGS[3]);
        boolean strong = Boolean.parseBoolean(ARGS[4]);
        int iters = Integer.parseInt(ARGS[5]), ov = Integer.parseInt(ARGS[6]);
        THREADS = Integer.parseInt(ARGS[7]);
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        File pf = new File(PROJ, "conversations.gephi");
        Project p = pc.openProject(pf);
        Workspace target = null;
        for (Workspace w : p.getLookup().lookup(WorkspaceProvider.class).getWorkspaces()) {
            WorkspaceInformation info = w.getLookup().lookup(WorkspaceInformation.class);
            if (info != null && info.getName().startsWith("30 largest")) target = w;
        }
        pc.openWorkspace(target);
        GraphModel gm = gc.getGraphModel(target);
        Graph g = gm.getGraph();
        log("relayout conv figure workspace: nodes=" + g.getNodeCount() + " edges=" + g.getEdgeCount());
        seedPositions(g, 3000);
        String lay = fa2(gm, iters, scaling, gravity, strong, false, 1.0, ov);
        try (PrintWriter w = new PrintWriter(new File(STATS, "conv_layout_settings.txt"), "UTF-8")) { w.println(lay); w.println("size = 3 + 27*sqrt(indegree/maxIndegree); colour = Subreddit; 30 largest weak components; labels off (TextPreview never imported)"); }
        basePreview(target, 60f, 1.5f, new EdgeColor(EdgeColor.Mode.SOURCE), false);
        exportFigure(target, "conversation_largest_components", 4000, 4000, true);
        save(p, pf);
    }

    static final String LWCC_STYLE = "size = Ranking InWeightRetained linear 5..30; colour = modularity_class (resolution 1.0 baseline): 8 largest classes fixed palette, other 58 classes grey #C8C8C8";

    /** Full-network workspace (14,507 users): strong-gravity FA2 so it is readable when opened in Desktop. */
    static String layoutFullAuthors(GraphModel gm1) {
        seedPositions(gm1.getGraph(), 2000);
        return fa2(gm1, 1500, 10, 1.0, true, false, 1.0, 200);
    }

    /** Colour full-network nodes like the LWCC figure: top-8 group colours, other LWCC groups grey, users outside the LWCC light grey. */
    static void colourFullFromLwcc(Graph g1, Graph g2) {
        Map<Object, Color> m = new HashMap<>();
        for (Node n : g2.getNodes()) m.put(n.getId(), n.getColor());
        Color outside = hex("#E2E2E2");
        for (Node n : g1.getNodes()) n.setColor(m.getOrDefault(n.getId(), outside));
    }

    /** Conversation full-network workspace: same FA2 settings as the 30-component figure workspace. */
    static String layoutConvWs0(GraphModel gm, Workspace ws) {
        seedPositions(gm.getGraph(), 3000);
        String s = fa2(gm, 2000, 1, 8.0, false, false, 1.0, 200);
        basePreview(ws, 60f, 1.5f, new EdgeColor(EdgeColor.Mode.SOURCE), false);
        return s;
    }

    static Workspace findWs(Project p, String prefix) {
        for (Workspace w : p.getLookup().lookup(WorkspaceProvider.class).getWorkspaces()) {
            WorkspaceInformation info = w.getLookup().lookup(WorkspaceInformation.class);
            if (info != null && info.getName().startsWith(prefix)) return w;
        }
        throw new IllegalStateException("workspace not found: " + prefix);
    }

    static String extent(Graph g) {
        float minx = Float.MAX_VALUE, maxx = -Float.MAX_VALUE; int zero = 0;
        for (Node n : g.getNodes()) { minx = Math.min(minx, n.x()); maxx = Math.max(maxx, n.x()); if (n.x() == 0f && n.y() == 0f) zero++; }
        Map<String, Integer> cc = new TreeMap<>();
        for (Node n : g.getNodes()) { Color c = n.getColor(); cc.merge(String.format("#%02X%02X%02X", c.getRed(), c.getGreen(), c.getBlue()), 1, Integer::sum); }
        String cols = cc.size() <= 12 ? ", colours " + cc : ", distinct colours " + cc.size();
        return "x extent " + minx + " .. " + maxx + ", nodes at (0,0) = " + zero + cols;
    }

    /** Fix round: recolour the non-top-8 LWCC groups grey WITHOUT moving any node, re-export the figure,
     *  and give the full-network workspace a readable layout and the same colours. Positions of the LWCC workspace are untouched. */
    static void recolorAuthors() throws Exception {
        THREADS = 4;
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        File pf = new File(PROJ, "author_replies.gephi");
        Project p = pc.openProject(pf);
        Workspace lw = findWs(p, "Largest"), fw = findWs(p, "Full");
        Graph g2 = gc.getGraphModel(lw).getGraph();
        LinkedHashMap<Integer, Integer> sizes = classSizes(g2, Modularity.MODULARITY_CLASS);
        log("recolor LWCC: nodes=" + g2.getNodeCount() + " edges=" + g2.getEdgeCount() + " classes=" + sizes.size() + " " + extent(g2));
        Map<Integer, Color> col = new HashMap<>();
        int r = 0; for (Integer c : sizes.keySet()) { col.put(c, r < 8 ? TOP8[r] : GREY); r++; }
        int changed = 0, topMismatch = 0;
        Set<Color> top8 = new HashSet<>(Arrays.asList(TOP8));
        for (Node n : g2.getNodes()) {
            Color old = n.getColor(), nw = col.get(((Number) n.getAttribute(Modularity.MODULARITY_CLASS)).intValue());
            if (top8.contains(nw) && !nw.equals(old)) topMismatch++;
            if (!nw.equals(old)) { n.setColor(nw); changed++; }
        }
        log("  recoloured nodes=" + changed + " (top-8 colour mismatches vs saved project=" + topMismatch + ")");
        try (PrintWriter w = new PrintWriter(new File(STATS, "authors_lwcc_palette.csv"), "UTF-8")) {
            w.println("rank,modularity_class,users,hex");
            int k = 0; for (Map.Entry<Integer, Integer> e : sizes.entrySet()) { Color c = col.get(e.getKey()); w.printf("%d,%d,%d,#%02X%02X%02X%n", ++k, e.getKey(), e.getValue(), c.getRed(), c.getGreen(), c.getBlue()); }
        }
        pc.openWorkspace(lw);
        basePreview(lw, 45f, 1.5f, new EdgeColor(EdgeColor.Mode.MIXED), false);
        exportFigure(lw, "largest_component_communities", 4000, 4000, true);
        exportGexf(lw, new File(PROJ, "author_replies_largest_component.gexf"));
        log("  after export " + extent(g2));
        // full-network workspace
        GraphModel gm1 = gc.getGraphModel(fw);
        Graph g1 = gm1.getGraph();
        log("full network workspace: nodes=" + g1.getNodeCount() + " edges=" + g1.getEdgeCount() + " before " + extent(g1));
        pc.openWorkspace(fw);
        String lay1 = layoutFullAuthors(gm1);
        colourFullFromLwcc(g1, g2);
        basePreview(fw, 30f, 1.0f, new EdgeColor(EdgeColor.Mode.MIXED), false);
        log("  after layout " + extent(g1));
        try (PrintWriter w = new PrintWriter(new File(STATS, "authors_full_layout_settings.txt"), "UTF-8")) {
            w.println(lay1);
            w.println("Full-network workspace only (no figure exported). Colour: LWCC users as in the LWCC figure (8 largest groups, others #C8C8C8); users outside the LWCC #E2E2E2. Size 4 + 0.15 x InWeightRetained.");
        }
        pc.openWorkspace(lw);
        save(p, pf);
    }

    /** Fix round: lay out the conversation full-network workspace (it was saved with every node at (0,0)). The figure workspace is not touched. */
    static void layoutConvFull() throws Exception {
        THREADS = 4;
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        File pf = new File(PROJ, "conversations.gephi");
        Project p = pc.openProject(pf);
        Workspace w0 = findWs(p, "Conversation network"), w1 = findWs(p, "30 largest");
        GraphModel gm = gc.getGraphModel(w0);
        log("conv full workspace: nodes=" + gm.getGraph().getNodeCount() + " edges=" + gm.getGraph().getEdgeCount() + " before " + extent(gm.getGraph()));
        log("conv figure workspace before: " + extent(gc.getGraphModel(w1).getGraph()));
        pc.openWorkspace(w0);
        String lay = layoutConvWs0(gm, w0);
        log("  after layout " + extent(gm.getGraph()));
        try (PrintWriter w = new PrintWriter(new File(STATS, "conv_full_layout_settings.txt"), "UTF-8")) { w.println(lay); w.println("Full conversation workspace only (no figure exported); colour = Subreddit; labels off."); }
        log("conv figure workspace after (must be unchanged): " + extent(gc.getGraphModel(w1).getGraph()));
        pc.openWorkspace(w1);
        save(p, pf);
    }

    // ------------------------------------------------------------------ verify
    static void runVerify(String only) throws Exception {
        ProjectController pc = lk(ProjectController.class);
        GraphController gc = lk(GraphController.class);
        File[] fs = PROJ.listFiles((dd, n) -> n.endsWith(".gephi"));
        Arrays.sort(fs);
        for (File f : fs) {
            if (only != null && !f.getName().equals(only)) continue;
            Project p = pc.openProject(f);
            int wi = 0;
            for (Workspace w : p.getLookup().lookup(WorkspaceProvider.class).getWorkspaces()) {
                GraphModel gm = gc.getGraphModel(w);
                Graph g = gm.getGraph();
                WorkspaceInformation info = w.getLookup().lookup(WorkspaceInformation.class);
                Column mc = gm.getNodeTable().getColumn(Modularity.MODULARITY_CLASS);
                String mod = mc == null ? "" : " modularityClasses=" + classSizes(g, Modularity.MODULARITY_CLASS).size();
                log(String.format(Locale.ROOT, "VERIFY %s ws%d '%s': nodes=%d edges=%d weightSum=%s directed=%b nodeCols=%d%s; %s",
                        f.getName(), wi++, info == null ? "?" : info.getName(), g.getNodeCount(), g.getEdgeCount(), fmtNum(weightSum(g)), gm.isDirected(), gm.getNodeTable().countColumns(), mod, extent(g)));
            }
            pc.closeCurrentProject();
        }
    }
}

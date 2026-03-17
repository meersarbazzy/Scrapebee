import streamlit as st
import os
import pandas as pd
import zipfile
import io
import requests
import time
import tempfile
import shutil
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from scrapebee.core.base_scraper import fetch_page, extract_content, save_to_docx, crawl_domain
from scrapebee.core.universal_scraper import TIPPScraperFinal
from scrapebee.core.pdf_processor import process_pdf_in_memory, create_text_pdf, process_pdf_pages
from pypdf import PdfReader

# --- Page Config (MUST BE FIRST) ---
favicon_path = os.path.join(os.path.dirname(__file__), "assets", "feviconicon.svg")
page_icon = favicon_path if os.path.exists(favicon_path) else "🐝"
st.set_page_config(page_title="ScrapeBee - Ultimate Web & PDF Toolset", page_icon=page_icon, layout="wide")

# --- Custom Styling (Branding) ---
st.markdown("""
<style>
    /* Global ScrapeBee Green Theme */
    :root {
        --sb-green: #007a3f;
    }
    
    /* Center align logo text if SVG fails */
    .stApp h1 {
        text-align: center;
    }

    /* Style all Buttons */
    div.stButton > button {
        background-color: var(--sb-green) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #005a2f !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px);
    }
    
    /* Style Download Buttons specifically (sometimes they look different) */
    div.stDownloadButton > button {
        background-color: var(--sb-green) !important;
        color: white !important;
        border-radius: 8px !important;
    }

    /* Style Radio Buttons */
    /* Selected radio indicator */
    div[data-baseweb="radio"] div[aria-checked="true"] > div:first-child {
        border-color: var(--sb-green) !important;
    }
    div[data-baseweb="radio"] div[aria-checked="true"] > div:first-child > div {
        background-color: var(--sb-green) !important;
    }
    
    /* Radio label text color when selected */
    div[data-baseweb="radio"] label[data-active="true"] {
        color: var(--sb-green) !important;
        font-weight: bold;
    }

    /* Custom scrollbar for professional feel */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--sb-green);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #005a2f;
    }
</style>
""", unsafe_allow_html=True)

# --- App Navigation & Branding ---
logo_path = os.path.join(os.path.dirname(__file__), "assets", "Scrape_bee_logo.svg")

if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.sidebar.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/svg+xml;base64,{data}" width="120">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown("<h1 style='text-align: center; color: #FFD700;'>🐝 ScrapeBee</h1>", unsafe_allow_html=True)

st.sidebar.title("🛠️ Tools Navigation")
app_mode = st.sidebar.radio("Choose Tool", ["Web Scraper", "Doc Extractor", "PDF Editor", "Glossary"])

# ---------------------------------------------------------------------
# --- WEB SCRAPER APP (SCRAPEBEE) ---
# ---------------------------------------------------------------------
def web_scraper_app():
    st.title("🐝 ScrapeBee: Web Scraper to Word")
    
    # Sidebar for Scraper Mode Selection
    mode = st.sidebar.radio("Select Scraper Mode", ["Batch List (Manual)", "Crawl Website (Auto)"])

    if st.sidebar.button("🗑️ Clear Scraper History"):
        st.session_state['results'] = []
        st.session_state['generated_files'] = []
        st.session_state['history_cleared'] = True
        st.rerun()

    # --- Session State Fixes ---
    if 'results' not in st.session_state: st.session_state['results'] = []
    if 'generated_files' not in st.session_state: st.session_state['generated_files'] = []
    if 'temp_outputs' not in st.session_state:
        st.session_state['temp_outputs'] = tempfile.mkdtemp(prefix="scrapebee_")

    OUTPUT_DIR = st.session_state['temp_outputs']
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Auto-Load existing metadata if state is empty but file exists AND not explicitly cleared
    metadata_path = os.path.join(OUTPUT_DIR, "metadata.xlsx")
    if not st.session_state['results'] and os.path.exists(metadata_path) and not st.session_state.get('history_cleared', False):
        try:
            df_existing = pd.read_excel(metadata_path)
            # Populate session state
            temp_results = []
            temp_files = []
            for index, row in df_existing.iterrows():
                local_path = str(row.get('Local_File_Path', ''))
                full_path = os.path.join(OUTPUT_DIR, local_path)
                temp_files.append(full_path)
                
                temp_results.append({
                     "Page Title": row.get('Entity_Title'),
                     "Page Link": row.get('TIPP_Source_URL'),
                     "Status": "Success" if os.path.exists(full_path) else "Missing",
                     "Scraped File": os.path.basename(local_path),
                     "Reference Link": row.get('External_Reference_URL')
                })
            st.session_state['results'] = temp_results
            st.session_state['generated_files'] = temp_files
        except Exception as e:
            print(f"Failed to auto-load: {e}")

    urls_to_process = []

    if mode == "Batch List (Manual)":
        st.markdown("Enter multiple URLs (one per line) to scrape content.")
        urls_input = st.text_area("Enter URLs:", placeholder="https://example.com/page1\nhttps://example.com/page2", height=200)
        if urls_input:
            urls_to_process = [u.strip() for u in urls_input.splitlines() if u.strip()]
            
    else:
        st.markdown("Enter a **starting URL**. The scraper will automatically find and scrape all pages on the same domain.")
        start_url = st.text_input("Start URL:", placeholder="https://tipp.gov.pk/")
        max_pages = st.number_input("Max Pages limit:", min_value=1, max_value=500, value=50)
        
        if st.button("Generate Crawl List", type="secondary"):
            if start_url:
                with st.status("Crawling domain for links...", expanded=True):
                    pass

    if st.button("Start Scraping", type="primary"):
        if mode == "Crawl Website (Auto)":
             if not start_url:
                 st.error("Please enter a start URL.")
             else:
                 is_tipp = "tipp.gov.pk" in start_url
                 scraper_type = "TIPP Specialized Scraper" if is_tipp else "Universal Generic Scraper"
                 st.info(f"Activated: **{scraper_type}** for {start_url}")
                 p_bar = st.progress(0, text="Initializing...")
                 def progress_callback(current, total, message):
                     pct = current / total if total > 0 else 0
                     if pct > 1: pct = 1
                     p_bar.progress(pct, text=f"{int(pct*100)}% - {message}")
                 with st.status(f"Crawling with {scraper_type}...", expanded=True) as status:
                    output_folder = OUTPUT_DIR
                    if is_tipp:
                        scraper = TIPPScraperFinal(output_dir=output_folder, progress_callback=progress_callback)
                    else:
                        from scrapebee.core.generic_scraper import GenericModScraper
                        scraper = GenericModScraper(start_url=start_url, max_pages=max_pages, output_dir=output_folder, progress_callback=progress_callback)
                    scraper.run()
                    status.update(label="Crawl Complete!", state="complete")
                    p_bar.progress(1.0, text="Completed!")
                 st.session_state['results'] = []
                 st.session_state['generated_files'] = []
                 if hasattr(scraper, 'metadata'):
                     for item in scraper.metadata:
                         full_path = os.path.join(output_folder, item['Local_File_Path'])
                         st.session_state['generated_files'].append(full_path)
                         st.session_state['results'].append({
                             "Page Title": item['Entity_Title'],
                             "Page Link": item['TIPP_Source_URL'],
                             "Status": "Success" if item['Local_File_Path'] else "Failed",
                             "Scraped File": os.path.basename(item['Local_File_Path'])
                         })
        else: # Batch Mode
            urls = urls_to_process
            if not urls:
                st.error("Please enter valid URLs.")
            else:
                st.session_state['results'] = []
                st.session_state['generated_files'] = []
                with st.status("Batch Scraping...", expanded=True) as status:
                    output_folder = os.path.join(os.getcwd(), "data", "outputs")
                    for i, url in enumerate(urls):
                        st.write(f"Processing ({i+1}/{len(urls)}): {url}")
                        try:
                            if "tipp.gov.pk" in url:
                                scraper = TIPPScraperFinal(output_dir=output_folder)
                                scraper.process_single_url(url)
                                scraper.save_excel()
                                current_metadata = scraper.metadata
                            else:
                                from scrapebee.core.generic_scraper import GenericModScraper
                                gen_scraper = GenericModScraper(start_url=url, max_pages=1, output_dir=output_folder)
                                gen_scraper.process_page(url)
                                gen_scraper.save_excel()
                                current_metadata = gen_scraper.metadata
                        except Exception as e:
                            st.write(f"❌ Error: {e}")
                            current_metadata = []
                        for item in current_metadata:
                            full_path = os.path.join(output_folder, item['Local_File_Path'])
                            st.session_state['generated_files'].append(full_path)
                            st.session_state['results'].append({
                                "Page Title": item['Entity_Title'],
                                "Page Link": item['TIPP_Source_URL'],
                                "Status": "Success" if item['Local_File_Path'] else "Failed",
                                "Scraped File": os.path.basename(item['Local_File_Path']),
                                "Reference Link": item['External_Reference_URL']
                            })
                    status.update(label="Batch Scraping Complete!", state="complete", expanded=False)

    if st.session_state['results']:
        st.success(f"Processing complete! {len(st.session_state['generated_files'])} files created.")
        df = pd.DataFrame(st.session_state['results'])
        st.subheader("Scraping Report")
        st.dataframe(df)
        st.subheader("Downloads")
        # Removed local path info as per user request
        col1, col2 = st.columns(2)
        excel_filename = "scraping_metadata.xlsx"
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        col1.download_button("📥 Download Metadata (Excel)", data=excel_buffer.getvalue(), file_name=excel_filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if st.session_state['generated_files']:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for file_path in st.session_state['generated_files']:
                    if os.path.exists(file_path):
                        rel_path = os.path.relpath(file_path, OUTPUT_DIR)
                        zip_file.write(file_path, rel_path)
            col2.download_button("📦 Download All Scraped Assets (ZIP)", data=zip_buffer.getvalue(), file_name="ScrapeBee_Collection.zip", mime="application/zip")

# ---------------------------------------------------------------------
# --- UNIVERSAL DOCUMENT EXTRACTOR APP ---
# ---------------------------------------------------------------------
def universal_document_app():
    st.title("🎯 Doc Extractor")
    st.write("Find, clean and download PDFs from any website — in batch or auto-crawl mode.")

    from scrapebee.core.pdf_processor import UniversalDocumentExtractor
    from urllib.parse import urlparse
    import io, zipfile, os

    mode = st.sidebar.radio("Extractor Mode", ["🔗 Batch URLs", "🕸️ Auto Crawl"])

    if st.sidebar.button("🗑️ Clear Extraction History"):
        st.session_state['batch_pdfs'] = {}
        st.session_state['batch_metadata'] = []
        st.session_state['crawl_pdfs'] = {}
        st.session_state['crawl_metadata'] = []
        st.rerun()

    def build_download_zip(pdf_dict, convert_to_word):
        from scrapebee.core.pdf_processor import pdf_to_word
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_f:
            for pdf_url, pdf_bytes in pdf_dict.items():
                base = os.path.basename(urlparse(pdf_url).path) or "document"
                if convert_to_word:
                    word_buf, _ = pdf_to_word(pdf_bytes)
                    fname = os.path.splitext(base)[0] + ".docx"
                    zip_f.writestr(fname, word_buf.read() if word_buf else pdf_bytes)
                else:
                    fname = base if base.endswith('.pdf') else base + ".pdf"
                    zip_f.writestr(fname, pdf_bytes)
        return zip_buffer.getvalue()

    if mode == "🔗 Batch URLs":
        st.subheader("Batch Mode — Extract PDFs")
        raw_urls = st.text_area("Enter URLs (one per line)", height=150, placeholder="https://example.com/manuals")

        if st.button("🚀 Extract PDFs", key="batch_go", use_container_width=True) and raw_urls.strip():
            urls = [u.strip() for u in raw_urls.strip().splitlines() if u.strip()]
            all_pdfs = {}
            with st.status("🔍 Scanning URLs...", expanded=True) as status:
                for i, url in enumerate(urls):
                    st.write(f"Scanning: `{url}`")
                    extractor = UniversalDocumentExtractor(url, max_pages=1, direct_only=True)
                    extractor.run()
                    all_pdfs.update(extractor.discovered_pdfs)
                status.update(label=f"Scan complete. Found {len(all_pdfs)} PDF(s).", state="complete")
            st.session_state['batch_pdfs'] = all_pdfs
            st.session_state['batch_metadata'] = extractor.metadata

        if 'batch_pdfs' in st.session_state and st.session_state['batch_pdfs']:
            all_pdfs = st.session_state['batch_pdfs']
            st.success(f"✅ Found {len(all_pdfs)} document(s).")
            with st.expander("📋 View List"):
                for i, url in enumerate(all_pdfs.keys(), 1):
                    st.write(f"{i}. `{url}`")
            
            convert_word = st.checkbox("📝 Also convert to Word (.docx)", key="batch_convert")
            if st.button("📥 Download Results (ZIP)", key="batch_dl_final", use_container_width=True):
                with st.spinner("Preparing ZIP..."):
                    data = build_download_zip(all_pdfs, convert_word)
                fname = "ScrapeBee_Batch_Word.zip" if convert_word else "ScrapeBee_Batch_PDFs.zip"
                st.download_button("⬇️ Click to Save ZIP", data=data, file_name=fname, use_container_width=True)
            
            if 'batch_metadata' in st.session_state and st.session_state['batch_metadata']:
                df_meta = pd.DataFrame(st.session_state['batch_metadata'])
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
                    df_meta.to_excel(writer, index=False)
                st.download_button("📥 Download Document Metadata (Excel)", data=excel_buf.getvalue(), file_name="extraction_metadata.xlsx", use_container_width=True)

    else:  # Auto Crawl mode
        st.subheader("Auto Crawl Mode — Discover PDFs")
        target_url = st.text_input("Enter Start URL", placeholder="https://www.psw.gov.pk")
        depth = st.number_input("Max Pages", min_value=1, max_value=200, value=20)

        if st.button("🕸️ Start Crawl", key="crawl_go", use_container_width=True) and target_url:
            p_bar = st.progress(0)
            def progress_callback(curr, total, msg):
                pct = min(curr / total, 1.0) if total > 0 else 0
                p_bar.progress(pct, text=f"{int(pct*100)}% — {msg}")

            extractor = UniversalDocumentExtractor(target_url, max_pages=depth, progress_callback=progress_callback)
            with st.status("🕸️ Crawling...", expanded=True) as status:
                extractor.run()
                status.update(label=f"Done! Found {len(extractor.discovered_pdfs)} PDF(s).", state="complete")
            st.session_state['crawl_pdfs'] = extractor.discovered_pdfs
            st.session_state['crawl_metadata'] = extractor.metadata

        if 'crawl_pdfs' in st.session_state and st.session_state['crawl_pdfs']:
            crawl_pdfs = st.session_state['crawl_pdfs']
            st.success(f"✅ Discovered {len(crawl_pdfs)} document(s).")
            with st.expander("📋 View List"):
                for i, url in enumerate(crawl_pdfs.keys(), 1):
                    st.write(f"{i}. `{url}`")

            convert_word = st.checkbox("📝 Also convert to Word (.docx)", key="crawl_convert")
            if st.button("📥 Download Results (ZIP)", key="crawl_dl_final", use_container_width=True):
                with st.spinner("Preparing ZIP..."):
                    data = build_download_zip(crawl_pdfs, convert_word)
                fname = "ScrapeBee_Crawl_Word.zip" if convert_word else "ScrapeBee_Crawled_PDFs.zip"
                st.download_button("⬇️ Click to Save ZIP", data=data, file_name=fname, use_container_width=True)

            if 'crawl_metadata' in st.session_state and st.session_state['crawl_metadata']:
                df_meta = pd.DataFrame(st.session_state['crawl_metadata'])
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
                    df_meta.to_excel(writer, index=False)
                st.download_button("📥 Download Document Metadata (Excel)", data=excel_buf.getvalue(), file_name="crawled_extraction_metadata.xlsx", use_container_width=True)

# ---------------------------------------------------------------------
# --- PDF EDITOR APP ---
# ---------------------------------------------------------------------
def pdf_editor_app():
    st.title("🛠️ ScrapeBee PDF Editor")
    st.write("Professional-grade PDF page manipulation and universal format conversion.")
    
    tab1, tab2, tab3 = st.tabs(["📄 Document Transformation", "🚀 Universal Converter", "📦 Universal Compressor"])
    
    with tab1:
        st.subheader("Transform & Rearrange")
        col1, col2 = st.columns([2, 1])
        with col1:
            uploaded_file = st.file_uploader("Upload PDF File", type="pdf", key="editor_uploader")
            page_order = st.text_input("Rearrange Pages", placeholder="e.g. 1, 3, 2, 5", help="Comma-separated page numbers. Omit to delete, repeat to duplicate.")
        with col2:
            st.info("💡 **Tips:**\n- Leave empty to keep all pages.\n- Reorder: `2,1,3`\n- Duplicate: `1,1,2`")
        
        user_text = st.text_area("Append New Text Page", placeholder="Type content here to create a new page at the end of your PDF...", height=150)

        if st.button("🚀 Process & Generate PDF") and uploaded_file:
            try:
                reader = PdfReader(uploaded_file)
                final_buffer, messages = process_pdf_pages(reader, page_order, user_text)
                for msg in messages: st.warning(msg)
                st.success("ScrapeBee has successfully processed your PDF!")
                st.download_button("📥 Download Enhanced PDF", data=final_buffer, file_name=f"scrapebee_{uploaded_file.name}")
            except Exception as e:
                st.error(f"Failed to process PDF: {e}")

    with tab2:
        st.subheader("Universal Conversion Suite")
        st.write("Convert between PDF and various professional formats with high fidelity.")
        
        conv_type = st.selectbox("Select Conversion Type", [
            "📄 PDF → Word (.docx)",
            "📊 PDF → Excel (.xlsx)",
            "🖼️ PDF → Images (PNG)",
            "📝 Word (.docx) → PDF",
            "📉 Excel (.xlsx) → PDF",
            "📸 Images → PDF"
        ])
        
        # Determine uploader type based on selection
        if "PDF →" in conv_type:
            up_label, up_type = "Upload PDF", ["pdf"]
        elif "Word" in conv_type:
            up_label, up_type = "Upload Word Document", ["docx"]
        elif "Excel" in conv_type:
            up_label, up_type = "Upload Excel Spreadsheet", ["xlsx"]
        else: # Images
            up_label, up_type = "Upload Images", ["png", "jpg", "jpeg"]
        
        multiple = "Images" in conv_type
        conv_file = st.file_uploader(up_label, type=up_type, key="conv_uploader", accept_multiple_files=multiple)

        if st.button("⚡ Start Professional Conversion") and conv_file:
            from scrapebee.core import pdf_processor as pp
            with st.spinner("Processing... ScrapeBee is working its magic."):
                try:
                    if conv_type == "📄 PDF → Word (.docx)":
                        res_buf, ocr = pp.pdf_to_word(conv_file.read())
                        fname = os.path.splitext(conv_file.name)[0] + ".docx"
                        if ocr: st.info("ℹ️ Scanned PDF detected — High-precision OCR utilized.")
                        st.success("✅ Conversion complete!")
                        st.download_button("📥 Download Word Document", data=res_buf, file_name=fname)
                        
                    elif conv_type == "📊 PDF → Excel (.xlsx)":
                        res_buf = pp.pdf_to_excel(conv_file.read())
                        fname = os.path.splitext(conv_file.name)[0] + ".xlsx"
                        st.success("✅ Conversion complete!")
                        st.download_button("📥 Download Excel File", data=res_buf, file_name=fname)
                        
                    elif conv_type == "🖼️ PDF → Images (PNG)":
                        res_buf = pp.pdf_to_images(conv_file.read())
                        fname = os.path.splitext(conv_file.name)[0] + "_images.zip"
                        st.success("✅ Image rendering complete!")
                        st.download_button("📥 Download Images (ZIP)", data=res_buf, file_name=fname)
                        
                    elif conv_type == "📝 Word (.docx) → PDF":
                        res_buf = pp.word_to_pdf(conv_file.read())
                        fname = os.path.splitext(conv_file.name)[0] + ".pdf"
                        st.success("✅ PDF generated successfully!")
                        st.download_button("📥 Download PDF", data=res_buf, file_name=fname)
                        
                    elif conv_type == "📉 Excel (.xlsx) → PDF":
                        res_buf = pp.excel_to_pdf(conv_file.read())
                        fname = os.path.splitext(conv_file.name)[0] + ".pdf"
                        st.success("✅ PDF generated successfully!")
                        st.download_button("📥 Download PDF", data=res_buf, file_name=fname)
                        
                    elif conv_type == "📸 Images → PDF":
                        files_data = [f.read() for f in conv_file]
                        res_buf = pp.images_to_pdf(files_data)
                        st.success("✅ All images stitched into PDF successfully!")
                        st.download_button("📥 Download PDF", data=res_buf, file_name="ScrapeBee_Images.pdf")
                except Exception as e:
                    st.error(f"Conversion error: {e}")

    with tab3:
        st.subheader("📦 Universal File Compressor")
        st.write("Reduce file size using enterprise-grade optimization algorithms.")
        st.caption("Supported: **PDF, Word, Excel, CSV, Parquet**")
        
        comp_file = st.file_uploader("Upload File to Compress", type=["pdf", "docx", "xlsx", "csv", "parquet"], key="comp_uploader")
        
        if st.button("📉 Compress File", use_container_width=True) and comp_file:
            from scrapebee.core import pdf_processor as pp
            with st.spinner("Optimizing file size..."):
                try:
                    ext = os.path.splitext(comp_file.name)[1].lower()
                    res_buf = pp.compress_file(comp_file.read(), ext)
                    
                    # Handle CSV output extension (it becomes .gz if compressed)
                    out_fname = comp_file.name
                    if ext == '.csv': out_fname += ".gz"
                    
                    st.success(f"✅ Optimization complete!")
                    st.download_button("⬇️ Download Optimized File", data=res_buf, file_name=out_fname, use_container_width=True)
                except Exception as e:
                    st.error(f"Compression error: {e}")

# ---------------------------------------------------------------------
# --- GLOSSARY & USER GUIDE ---
# ---------------------------------------------------------------------
def glossary_app():
    st.title("📚 ScrapeBee Glossary & Guide")
    st.warning("💡 **Tip:** Use the search bar below to quickly find tool features or technical definitions.")
    
    # Search Bar
    search_query = st.text_input("🔍 Search terminology or features...", placeholder="e.g. OCR, Scraper, Storage...")
    st.markdown("---")
    # Glossary Data
    glossary_items = [
        {
            "category": "🛠️ Tools",
            "title": "Web Scraper",
            "desc": "Extracts text and data from websites into Word. Supports **Batch Mode** (specific URLs) and **Auto-Crawl** (follows links on a domain)."
        },
        {
            "category": "🛠️ Tools",
            "title": "Doc Extractor",
            "desc": "An automated retrieval system that specializes in locating and harvesting PDF documents across complex domains while preserving metadata."
        },
        {
            "category": "🛠️ Tools",
            "title": "Universal Converter",
            "desc": "A specialized suite for high-fidelity **vice-versa** transformations: PDF to Word/Excel/Image, and Word/Excel/Image to PDF."
        },
        {
            "category": "🛠️ Tools",
            "title": "Universal Compressor",
            "desc": "Reduces file sizes for **PDF, Word, Excel, CSV, and Parquet** using enterprise-grade algorithms like ZSTD and high-level GZIP DEF-9."
        },
        {
            "category": "🛠️ Tools",
            "title": "PDF Editor",
            "desc": "Professional manipulation: **Reorder** pages, **Delete** noise, and **Append Text** pages instantly to existing documents."
        },
        {
            "category": "🧠 Terminology",
            "title": "OCR",
            "desc": "**Optical Character Recognition**. Automatically reads 'scanned' or image-based PDFs to turn them into editable text."
        },
        {
            "category": "🧠 Terminology",
            "title": "Redaction",
            "desc": "The automated process of masking or removing specific zones (like headers/footers) from a document."
        },
        {
            "category": "🧠 Terminology",
            "title": "YiiPager",
            "desc": "A specific technical pagination system found on government portals that ScrapeBee is optimized to navigate."
        },
        {
            "category": "🧠 Terminology",
            "title": "Headless",
            "desc": "Refers to running the web browser (Chrome) in the background without a visible window for faster automation."
        },
        {
            "category": "📂 Data",
            "title": "Ephemeral Storage",
            "desc": "ScrapeBee uses session-based temporary storage. Results are bundled into a ZIP for download and cleared automatically to keep your project clutter-free."
        },
        {
            "category": "🧠 Terminology",
            "title": "Zero-Clutter Policy",
            "desc": "A professional commitment to ephemeral storage. No project directory clutter—results are processed in temp folders and delivered via ZIP."
        },
        {
            "category": "⚡ Optimization",
            "title": "Batch Processing",
            "desc": "Handle multiple URLs simultaneously to save time. Perfect for large-scale data collection projects."
        },
        {
            "category": "🔒 Security",
            "title": "Headless Browsing",
            "desc": "Scrapers run in a 'headless' state, meaning no browser window pops up, making the process faster and more stable."
        }
    ]
    
    # Filter results
    filtered_items = [
        item for item in glossary_items 
        if search_query.lower() in item['title'].lower() or search_query.lower() in item['desc'].lower()
    ]
    
    if not filtered_items:
        st.warning(f"No results found for '{search_query}'")
    else:
        # Display as cards using columns
        for i in range(0, len(filtered_items), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(filtered_items):
                    item = filtered_items[i+j]
                    with cols[j]:
                        st.markdown(f"""
                        <div style="
                            padding: 20px;
                            border-radius: 10px;
                            border: 1px solid #008f4a;
                            background: linear-gradient(135deg, #007a3f 0%, #005a2e 100%);
                            margin-bottom: 20px;
                            height: 100%;
                            transition: transform 0.2s ease-in-out;
                        ">
                            <span style="color: #FFD700; font-size: 0.8rem; font-weight: bold;">{item['category']}</span>
                            <h3 style="margin-top: 5px; color: #fff;">{item['title']}</h3>
                            <p style="color: #ccc; font-size: 0.9rem; line-height: 1.4;">{item['desc']}</p>
                        </div>
                        """, unsafe_allow_html=True)

# --- Set Main Content based on Mode ---
if app_mode == "Web Scraper":
    web_scraper_app()
elif app_mode == "Doc Extractor":
    universal_document_app()
elif app_mode == "PDF Editor":
    pdf_editor_app()
else:
    glossary_app()

st.markdown("---")
st.caption("ScrapeBee - Powerful Web & Document Intelligence")

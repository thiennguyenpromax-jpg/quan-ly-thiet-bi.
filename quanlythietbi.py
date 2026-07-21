import streamlit as st
import pandas as pd
import os

# Cấu hình trang
st.set_page_config(page_title="Hệ Thống Quản Lý Thiết Bị & File", layout="wide")

# Đường dẫn lưu dữ liệu
GEAR_FILE = "thiet_bi.csv"
MEDIA_FILE = "danh_sach_file.csv"

# Khởi tạo file dữ liệu mẫu nếu chưa có
if not os.path.exists(GEAR_FILE):
    df_gear = pd.DataFrame(columns=["Tên thiết bị", "Tổng số lượng", "Đã mang đi", "Vị trí / Ghi chú"])
    df_gear.to_csv(GEAR_FILE, index=False)

if not os.path.exists(MEDIA_FILE):
    df_media = pd.DataFrame(columns=["Ngày quay", "Dự án / Tên Video", "Nơi lưu trữ (Ổ cứng/Cloud)", "Định dạng", "Ghi chú"])
    df_media.to_csv(MEDIA_FILE, index=False)

# Tiêu đề ứng dụng
st.title("🎬 Hệ Thống Quản Lý Thiết Bị & File Video")

# Tạo 2 Tab riêng biệt
tab1, tab2 = st.tabs(["📦 1. Quản Lý Thiết Bị Vật Lý", "📁 2. Quản Lý File Video"])

# ==========================================
# TAB 1: QUẢN LÝ THIẾT BỊ
# ==========================================
with tab1:
    st.header("Danh Sách & Trạng Thái Thiết Bị")
    
    # Đọc dữ liệu
    df_gear = pd.read_csv(GEAR_FILE)
    
    # Tính toán số lượng còn dư
    if not df_gear.empty:
        df_gear["Tổng số lượng"] = pd.to_numeric(df_gear["Tổng số lượng"], errors='coerce').fillna(0).astype(int)
        df_gear["Đã mang đi"] = pd.to_numeric(df_gear["Đã mang đi"], errors='coerce').fillna(0).astype(int)
        df_gear["Còn dư ở nhà"] = df_gear["Tổng số lượng"] - df_gear["Đã mang đi"]
        
        # Cảnh báo nếu số lượng mang đi vượt quá tổng số
        df_gear["Trạng thái"] = df_gear["Còn dư ở nhà"].apply(
            lambda x: "🟢 Sẵn sàng" if x > 0 else ("🔴 Hết hàng / Đã mang đi hết" if x == 0 else "⚠️ Lỗi số lượng")
        )
        
        st.dataframe(df_gear[["Tên thiết bị", "Tổng số lượng", "Đã mang đi", "Còn dư ở nhà", "Trạng thái", "Vị trí / Ghi chú"]], use_container_width=True)
    else:
        st.info("Chưa có thiết bị nào trong hệ thống.")

    st.divider()
    
    col1, col2 = st.columns(2)
    
    # Form thêm thiết bị mới
    with col1:
        st.subheader("➕ Thêm thiết bị mới")
        with st.form("add_gear_form"):
            name = st.text_input("Tên thiết bị (VD: Máy quay Sony A7S3, Đèn Godox...)")
            total_qty = st.number_input("Tổng số lượng sở hữu", min_value=1, value=1, step=1)
            location = st.text_input("Vị trí cất giữ (VD: Tủ A, Thùng số 2...)")
            submit_add = st.form_submit_button("Thêm thiết bị")
            
            if submit_add and name:
                new_row = pd.DataFrame([{"Tên thiết bị": name, "Tổng số lượng": total_qty, "Đã mang đi": 0, "Vị trí / Ghi chú": location}])
                df_gear = pd.concat([df_gear, new_row], ignore_index=False)
                df_gear.to_csv(GEAR_FILE, index=False)
                st.success(f"Đã thêm: {name}")
                st.rerun()

    # Form cập nhật số lượng mang đi làm
    with col2:
        st.subheader("🔄 Cập nhật đồ mang đi làm / trả về")
        if not df_gear.empty:
            with st.form("update_gear_form"):
                selected_item = st.selectbox("Chọn thiết bị", df_gear["Tên thiết bị"].tolist())
                
                # Lấy thông tin hiện tại
                current_take = int(df_gear.loc[df_gear["Tên thiết bị"] == selected_item, "Đã mang đi"].values[0])
                current_total = int(df_gear.loc[df_gear["Tên thiết bị"] == selected_item, "Tổng số lượng"].values[0])
                
                new_take = st.number_input("Số lượng ĐANG MANG ĐI LÀM", min_value=0, max_value=current_total, value=current_take, step=1)
                submit_update = st.form_submit_button("Cập nhật trạng thái")
                
                if submit_update:
                    df_gear.loc[df_gear["Tên thiết bị"] == selected_item, "Đã mang đi"] = new_take
                    df_gear.to_csv(GEAR_FILE, index=False)
                    st.success(f"Đã cập nhật trạng thái cho {selected_item}")
                    st.rerun()

# ==========================================
# TAB 2: QUẢN LÝ FILE VIDEO
# ==========================================
with tab2:
    st.header("Nhật Ký & Sắp Xếp File Video")
    
    df_media = pd.read_csv(MEDIA_FILE)
    
    # Tìm kiếm file
    search_term = st.text_input("🔍 Tìm kiếm video / dự án / ổ cứng lưu trữ:")
    if search_term:
        filtered_df = df_media[df_media.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df_media, use_container_width=True)

    st.divider()
    
    st.subheader("📝 Ghi chép lưu trữ file mới")
    with st.form("add_media_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            date = st.date_input("Ngày quay")
            project_name = st.text_input("Tên dự án / Nội dung quay (VD: Đi du lịch Đà Lạt, Quay đám cưới ABC)")
        with col_b:
            storage_loc = st.text_input("Nơi lưu file (VD: Ổ cứng Sandisk 1TB, Google Drive, Thẻ nhớ 2)")
            file_type = st.selectbox("Định dạng file", ["4K MP4", "1080p MP4", "RAW/LOG", "Khác"])
        
        notes = st.text_area("Ghi chú thêm (VD: Thư mục /2026/DaLat_Day1)")
        submit_media = st.form_submit_button("Lưu thông tin File")
        
        if submit_media and project_name:
            new_media = pd.DataFrame([{
                "Ngày quay": str(date),
                "Dự án / Tên Video": project_name,
                "Nơi lưu trữ (Ổ cứng/Cloud)": storage_loc,
                "Định dạng": file_type,
                "Ghi chú": notes
            }])
            df_media = pd.concat([df_media, new_media], ignore_index=False)
            df_media.to_csv(MEDIA_FILE, index=False)
            st.success("Đã lưu thông tin file!")
            st.rerun()
        df_file = pd.read_csv("danh_sach_file.csv")
        st.dataframe(df_file, use_container_width=True)
    else:
        st.info("Chưa tìm thấy dữ liệu file video.")

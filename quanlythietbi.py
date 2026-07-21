import os
import pandas as pd
import streamlit as st

# Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống Quản Lý Thiết Bị & File",
    page_icon="🎬",
    layout="wide",
)

GEAR_FILE = "thiet_bi.csv"
MEDIA_FILE = "danh_sach_file.csv"

# Khởi tạo file dữ liệu nếu chưa có
if not os.path.exists(GEAR_FILE):
    df_gear = pd.DataFrame(
        columns=[
            "Tên thiết bị",
            "Tổng số lượng",
            "Đã mang đi",
            "Vị trí / Ghi chú",
        ]
    )
    df_gear.to_csv(GEAR_FILE, index=False)

if not os.path.exists(MEDIA_FILE):
    df_media = pd.DataFrame(
        columns=[
            "Ngày quay",
            "Dự án / Tên Video",
            "Nơi lưu trữ (Ổ cứng/Cloud)",
            "Định dạng",
            "Ghi chú",
        ]
    )
    df_media.to_csv(MEDIA_FILE, index=False)

st.title("🎬 Hệ Thống Quản Lý Thiết Bị & File Video")

tab1, tab2 = st.tabs(["📦 1. Quản Lý Thiết Bị Vật Lý", "📁 2. Quản Lý File Video"])

# ==========================================
# TAB 1: QUẢN LÝ THIẾT BỊ
# ==========================================
with tab1:
    st.header("Danh Sách & Trạng Thái Thiết Bị")
    df_gear = pd.read_csv(GEAR_FILE)

    if not df_gear.empty:
        df_gear["Tổng số lượng"] = (
            pd.to_numeric(df_gear["Tổng số lượng"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        df_gear["Đã mang đi"] = (
            pd.to_numeric(df_gear["Đã mang đi"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        df_gear["Còn dư ở nhà"] = (
            df_gear["Tổng số lượng"] - df_gear["Đã mang đi"]
        )
        df_gear["Trạng thái"] = df_gear["Còn dư ở nhà"].apply(
            lambda x: "🟢 Sẵn sàng"
            if x > 0
            else ("🔴 Hết hàng / Đã mang đi" if x == 0 else "⚠️ Lỗi số lượng")
        )

        st.dataframe(
            df_gear[[
                "Tên thiết bị",
                "Tổng số lượng",
                "Đã mang đi",
                "Còn dư ở nhà",
                "Trạng thái",
                "Vị trí / Ghi chú",
            ]],
            use_container_width=True,
        )
    else:
        st.info("Chưa có thiết bị nào trong hệ thống.")

    st.divider()

    # Tạo 3 cột: Thêm | Sửa | Xóa
    col_add, col_edit, col_del = st.columns(3)

    # --- THÊM THIẾT BỊ ---
    with col_add:
        st.subheader("➕ Thêm thiết bị mới")
        with st.form("add_gear_form"):
            name = st.text_input("Tên thiết bị")
            total_qty = st.number_input(
                "Tổng số lượng sở hữu", min_value=1, value=1, step=1
            )
            location = st.text_input("Vị trí cất giữ / Ghi chú")
            submit_add = st.form_submit_button("Thêm mới")

            if submit_add and name:
                new_row = pd.DataFrame([{
                    "Tên thiết bị": name,
                    "Tổng số lượng": total_qty,
                    "Đã mang đi": 0,
                    "Vị trí / Ghi chú": location,
                }])
                df_gear = pd.concat(
                    [df_gear, new_row], ignore_index=True
                )
                df_gear.to_csv(GEAR_FILE, index=False)
                st.success(f"Đã thêm: {name}")
                st.rerun()

    # --- SỬA THIẾT BỊ ---
    with col_edit:
        st.subheader("✏️ Chỉnh sửa thiết bị")
        if not df_gear.empty:
            selected_edit = st.selectbox(
                "Chọn thiết bị cần sửa",
                df_gear["Tên thiết bị"].tolist(),
                key="edit_gear_select",
            )
            gear_info = df_gear[
                df_gear["Tên thiết bị"] == selected_edit
            ].iloc[0]

            with st.form("edit_gear_form"):
                edit_name = st.text_input(
                    "Tên thiết bị", value=gear_info["Tên thiết bị"]
                )
                edit_total = st.number_input(
                    "Tổng số lượng",
                    min_value=0,
                    value=int(gear_info["Tổng số lượng"]),
                )
                edit_taken = st.number_input(
                    "Số lượng đang mang đi",
                    min_value=0,
                    max_value=int(edit_total),
                    value=int(gear_info["Đã mang đi"]),
                )
                edit_loc = st.text_input(
                    "Vị trí / Ghi chú",
                    value=str(gear_info["Vị trí / Ghi chú"]),
                )
                submit_edit = st.form_submit_button("Lưu thay đổi")

                if submit_edit:
                    idx = df_gear[
                        df_gear["Tên thiết bị"] == selected_edit
                    ].index[0]
                    df_gear.loc[idx, "Tên thiết bị"] = edit_name
                    df_gear.loc[idx, "Tổng số lượng"] = edit_total
                    df_gear.loc[idx, "Đã mang đi"] = edit_taken
                    df_gear.loc[idx, "Vị trí / Ghi chú"] = edit_loc
                    df_gear.to_csv(GEAR_FILE, index=False)
                    st.success("Cập nhật thành công!")
                    st.rerun()

    # --- XÓA THIẾT BỊ ---
    with col_del:
        st.subheader("🗑️ Xóa thiết bị")
        if not df_gear.empty:
            selected_del = st.selectbox(
                "Chọn thiết bị cần xóa",
                df_gear["Tên thiết bị"].tolist(),
                key="del_gear_select",
            )
            if st.button("❌ Xác nhận xóa thiết bị", type="primary"):
                df_gear = df_gear[df_gear["Tên thiết bị"] != selected_del]
                df_gear.to_csv(GEAR_FILE, index=False)
                st.success(f"Đã xóa thiết bị: {selected_del}")
                st.rerun()

# ==========================================
# TAB 2: QUẢN LÝ FILE VIDEO
# ==========================================
with tab2:
    st.header("Nhật Ký & Sắp Xếp File Video")
    df_media = pd.read_csv(MEDIA_FILE)

    search_term = st.text_input(
        "🔍 Tìm kiếm video / dự án / ổ cứng lưu trữ:"
    )
    if search_term:
        filtered_df = df_media[
            df_media.apply(
                lambda row: row.astype(str)
                .str.contains(search_term, case=False)
                .any(),
                axis=1,
            )
        ]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df_media, use_container_width=True)

    st.divider()

    col_m_add, col_m_edit, col_m_del = st.columns(3)

    # --- THÊM FILE VIDEO ---
    with col_m_add:
        st.subheader("📝 Thêm file video mới")
        with st.form("add_media_form"):
            m_date = st.date_input("Ngày quay")
            m_project = st.text_input("Tên dự án / Nội dung quay")
            m_storage = st.text_input("Nơi lưu trữ (Ổ cứng, Cloud...)")
            m_type = st.selectbox(
                "Định dạng", ["4K MP4", "1080p MP4", "RAW/LOG", "Khác"]
            )
            m_notes = st.text_area("Ghi chú")
            submit_m_add = st.form_submit_button("Lưu File")

            if submit_m_add and m_project:
                new_media = pd.DataFrame([{
                    "Ngày quay": str(m_date),
                    "Dự án / Tên Video": m_project,
                    "Nơi lưu trữ (Ổ cứng/Cloud)": m_storage,
                    "Định dạng": m_type,
                    "Ghi chú": m_notes,
                }])
                df_media = pd.concat(
                    [df_media, new_media], ignore_index=True
                )
                df_media.to_csv(MEDIA_FILE, index=False)
                st.success("Đã lưu thông tin file!")
                st.rerun()

    # --- SỬA FILE VIDEO ---
    with col_m_edit:
        st.subheader("✏️ Chỉnh sửa thông tin file")
        if not df_media.empty:
            selected_m_edit = st.selectbox(
                "Chọn dự án cần sửa",
                df_media["Dự án / Tên Video"].tolist(),
                key="edit_media_select",
            )
            media_info = df_media[
                df_media["Dự án / Tên Video"] == selected_m_edit
            ].iloc[0]

            with st.form("edit_media_form"):
                e_m_project = st.text_input(
                    "Tên dự án", value=media_info["Dự án / Tên Video"]
                )
                e_m_storage = st.text_input(
                    "Nơi lưu trữ",
                    value=str(media_info["Nơi lưu trữ (Ổ cứng/Cloud)"]),
                )
                e_m_type = st.text_input(
                    "Định dạng", value=str(media_info["Định dạng"])
                )
                e_m_notes = st.text_area(
                    "Ghi chú", value=str(media_info["Ghi chú"])
                )
                submit_m_edit = st.form_submit_button("Lưu thay đổi")

                if submit_m_edit:
                    m_idx = df_media[
                        df_media["Dự án / Tên Video"] == selected_m_edit
                    ].index[0]
                    df_media.loc[m_idx, "Dự án / Tên Video"] = e_m_project
                    df_media.loc[m_idx, "Nơi lưu trữ (Ổ cứng/Cloud)"] = (
                        e_m_storage
                    )
                    df_media.loc[m_idx, "Định dạng"] = e_m_type
                    df_media.loc[m_idx, "Ghi chú"] = e_m_notes
                    df_media.to_csv(MEDIA_FILE, index=False)
                    st.success("Cập nhật file thành công!")
                    st.rerun()

    # --- XÓA FILE VIDEO ---
    with col_m_del:
        st.subheader("🗑️ Xóa thông tin file")
        if not df_media.empty:
            selected_m_del = st.selectbox(
                "Chọn dự án cần xóa",
                df_media["Dự án / Tên Video"].tolist(),
                key="del_media_select",
            )
            if st.button("❌ Xác nhận xóa dự án", type="primary"):
                df_media = df_media[
                    df_media["Dự án / Tên Video"] != selected_m_del
                ]
                df_media.to_csv(MEDIA_FILE, index=False)
                st.success(f"Đã xóa dự án: {selected_m_del}")
                st.rerun()

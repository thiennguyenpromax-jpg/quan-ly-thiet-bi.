import json
import os
import pandas as pd
import streamlit as st

# Cấu hình trang web
st.set_page_config(
    page_title="Hệ Thống Quản Lý Thiết Bị", page_icon="🎬", layout="wide"
)

# Đường dẫn lưu trữ dữ liệu tập trung trên Server
DATA_FILE = "data_store.json"


# Các hàm đọc/ghi dữ liệu JSON thuần Python
def load_all_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}


def save_all_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Quản lý Session Đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ==========================================
# MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 Đăng Nhập Hệ Thống Quản Lý")

    tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký tài khoản"])

    all_data = load_all_data()

    with tab_login:
        with st.form("login_form"):
            user_input = st.text_input("Tên đăng nhập")
            pass_input = st.text_input("Mật khẩu", type="password")
            btn_login = st.form_submit_button("Đăng nhập")

            if btn_login:
                if user_input in all_data:
                    if all_data[user_input]["password"] == pass_input:
                        st.session_state.logged_in = True
                        st.session_state.username = user_input
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")
                else:
                    st.error("Tài khoản không tồn tại!")

    with tab_register:
        with st.form("register_form"):
            reg_user = st.text_input("Tạo tên đăng nhập mới")
            reg_pass = st.text_input("Tạo mật khẩu", type="password")
            btn_reg = st.form_submit_button("Tạo tài khoản")

            if btn_reg:
                if not reg_user or not reg_pass:
                    st.warning("Vui lòng điền đầy đủ thông tin!")
                elif reg_user in all_data:
                    st.error("Tên đăng nhập này đã tồn tại!")
                else:
                    all_data[reg_user] = {
                        "password": reg_pass,
                        "gear": [],
                        "media": [],
                    }
                    save_all_data(all_data)
                    st.success("Đăng ký thành công! Bạn có thể đăng nhập ngay.")

# ==========================================
# MÀN HÌNH CHÍNH (SAU KHI ĐĂNG NHẬP)
# ==========================================
else:
    user = st.session_state.username
    all_data = load_all_data()
    user_data = all_data.get(user, {"gear": [], "media": []})

    # Thanh Tiêu Đề & Nút Đăng Xuất
    col_title, col_logout = st.columns([8, 2])
    with col_title:
        st.title(f"🎬 Quản Lý Thiết Bị & File - [Tài khoản: {user}]")
    with col_logout:
        st.write("")
        if st.button("🚪 Đăng xuất"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()

    tab1, tab2 = st.tabs(["📦 1. Quản Lý Thiết Bị", "📁 2. Quản Lý File Video"])

    # ------------------------------------------
    # TAB 1: QUẢN LÝ THIẾT BỊ
    # ------------------------------------------
    with tab1:
        st.header("Danh Sách Thiết Bị")
        gear_list = user_data.get("gear", [])
        df_gear = pd.DataFrame(gear_list)

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
                else (
                    "🔴 Hết hàng / Đã mang đi" if x == 0 else "⚠️ Lỗi số lượng"
                )
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
            st.info("Chưa có thiết bị nào.")

        st.divider()
        col_g_add, col_g_edit, col_g_del = st.columns(3)

        # Thêm thiết bị
        with col_g_add:
            st.subheader("➕ Thêm thiết bị")
            with st.form("add_g_form"):
                g_name = st.text_input("Tên thiết bị")
                g_total = st.number_input(
                    "Tổng số lượng", min_value=1, value=1
                )
                g_loc = st.text_input("Vị trí / Ghi chú")
                btn_g_add = st.form_submit_button("Thêm")

                if btn_g_add and g_name:
                    gear_list.append({
                        "Tên thiết bị": g_name,
                        "Tổng số lượng": g_total,
                        "Đã mang đi": 0,
                        "Vị trí / Ghi chú": g_loc,
                    })
                    all_data[user]["gear"] = gear_list
                    save_all_data(all_data)
                    st.success("Đã thêm thành công!")
                    st.rerun()

        # Sửa thiết bị
        with col_g_edit:
            st.subheader("✏️ Chỉnh sửa thiết bị")
            if gear_list:
                selected_g = st.selectbox(
                    "Chọn thiết bị", [item["Tên thiết bị"] for item in gear_list]
                )
                item_idx = next(
                    i
                    for i, item in enumerate(gear_list)
                    if item["Tên thiết bị"] == selected_g
                )

                with st.form("edit_g_form"):
                    e_g_name = st.text_input(
                        "Tên thiết bị", value=gear_list[item_idx]["Tên thiết bị"]
                    )
                    e_g_total = st.number_input(
                        "Tổng số lượng",
                        min_value=0,
                        value=int(gear_list[item_idx]["Tổng số lượng"]),
                    )
                    e_g_taken = st.number_input(
                        "Số lượng đang mang đi",
                        min_value=0,
                        max_value=int(e_g_total),
                        value=int(gear_list[item_idx]["Đã mang đi"]),
                    )
                    e_g_loc = st.text_input(
                        "Vị trí / Ghi chú",
                        value=str(gear_list[item_idx]["Vị trí / Ghi chú"]),
                    )
                    btn_g_edit = st.form_submit_button("Lưu thay đổi")

                    if btn_g_edit:
                        gear_list[item_idx] = {
                            "Tên thiết bị": e_g_name,
                            "Tổng số lượng": e_g_total,
                            "Đã mang đi": e_g_taken,
                            "Vị trí / Ghi chú": e_g_loc,
                        }
                        all_data[user]["gear"] = gear_list
                        save_all_data(all_data)
                        st.success("Cập nhật thành công!")
                        st.rerun()

        # Xóa thiết bị
        with col_g_del:
            st.subheader("🗑️ Xóa thiết bị")
            if gear_list:
                del_g = st.selectbox(
                    "Chọn thiết bị xóa",
                    [item["Tên thiết bị"] for item in gear_list],
                    key="del_g_key",
                )
                if st.button("❌ Xác nhận Xóa", type="primary"):
                    user_data["gear"] = [
                        item
                        for item in gear_list
                        if item["Tên thiết bị"] != del_g
                    ]
                    all_data[user] = user_data
                    save_all_data(all_data)
                    st.success("Đã xóa!")
                    st.rerun()

    # ------------------------------------------
    # TAB 2: QUẢN LÝ FILE VIDEO
    # ------------------------------------------
    with tab2:
        st.header("Danh Sách File Video")
        media_list = user_data.get("media", [])
        df_media = pd.DataFrame(media_list)

        search = st.text_input("🔍 Tìm kiếm video / dự án:")
        if not df_media.empty:
            if search:
                filtered = df_media[
                    df_media.apply(
                        lambda r: r.astype(str)
                        .str.contains(search, case=False)
                        .any(),
                        axis=1,
                    )
                ]
                st.dataframe(filtered, use_container_width=True)
            else:
                st.dataframe(df_media, use_container_width=True)
        else:
            st.info("Chưa có thông tin file video.")

        st.divider()
        col_m_add, col_m_edit, col_m_del = st.columns(3)

        # Thêm file video
        with col_m_add:
            st.subheader("📝 Thêm file video")
            with st.form("add_m_form"):
                m_date = st.date_input("Ngày quay")
                m_proj = st.text_input("Tên dự án")
                m_store = st.text_input("Nơi lưu trữ")
                m_type = st.selectbox(
                    "Định dạng", ["4K MP4", "1080p MP4", "RAW/LOG", "Khác"]
                )
                m_note = st.text_area("Ghi chú")
                btn_m_add = st.form_submit_button("Lưu File")

                if btn_m_add and m_proj:
                    media_list.append({
                        "Ngày quay": str(m_date),
                        "Dự án / Tên Video": m_proj,
                        "Nơi lưu trữ": m_store,
                        "Định dạng": m_type,
                        "Ghi chú": m_note,
                    })
                    all_data[user]["media"] = media_list
                    save_all_data(all_data)
                    st.success("Đã lưu thành công!")
                    st.rerun()

        # Sửa file video
        with col_m_edit:
            st.subheader("✏️ Chỉnh sửa file")
            if media_list:
                selected_m = st.selectbox(
                    "Chọn dự án",
                    [item["Dự án / Tên Video"] for item in media_list],
                )
                m_idx = next(
                    i
                    for i, item in enumerate(media_list)
                    if item["Dự án / Tên Video"] == selected_m
                )

                with st.form("edit_m_form"):
                    e_m_proj = st.text_input(
                        "Tên dự án",
                        value=media_list[m_idx]["Dự án / Tên Video"],
                    )
                    e_m_store = st.text_input(
                        "Nơi lưu trữ",
                        value=str(media_list[m_idx]["Nơi lưu trữ"]),
                    )
                    e_m_type = st.text_input(
                        "Định dạng", value=str(media_list[m_idx]["Định dạng"])
                    )
                    e_m_note = st.text_area(
                        "Ghi chú", value=str(media_list[m_idx]["Ghi chú"])
                    )
                    btn_m_edit = st.form_submit_button("Lưu thay đổi")

                    if btn_m_edit:
                        media_list[m_idx] = {
                            "Ngày quay": media_list[m_idx]["Ngày quay"],
                            "Dự án / Tên Video": e_m_proj,
                            "Nơi lưu trữ": e_m_store,
                            "Định dạng": e_m_type,
                            "Ghi chú": e_m_note,
                        }
                        all_data[user]["media"] = media_list
                        save_all_data(all_data)
                        st.success("Đã cập nhật!")
                        st.rerun()

        # Xóa file video
        with col_m_del:
            st.subheader("🗑️ Xóa file")
            if media_list:
                del_m = st.selectbox(
                    "Chọn dự án xóa",
                    [item["Dự án / Tên Video"] for item in media_list],
                    key="del_m_key",
                )
                if st.button("❌ Xác nhận Xóa File", type="primary"):
                    user_data["media"] = [
                        item
                        for item in media_list
                        if item["Dự án / Tên Video"] != del_m
                    ]
                    all_data[user] = user_data
                    save_all_data(all_data)
                    st.success("Đã xóa!")
                    st.rerun()

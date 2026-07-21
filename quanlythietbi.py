import json
import os
import extra_streamlit_components as stx
import pandas as pd
import streamlit as st

# Cấu hình trang web
st.set_page_config(
    page_title="Hệ Thống Quản Lý Thiết Bị", page_icon="🎬", layout="wide"
)

# Đường dẫn lưu trữ dữ liệu tập trung trên Server
DATA_FILE = "data_store.json"

cookie_manager = get_cookie_manager()

# Các hàm đọc/ghi dữ liệu JSON
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


# Quản lý Session & Cookie Đăng nhập
auth_cookie = cookie_manager.get(cookie="user_auth")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Tự động đăng nhập nếu tìm thấy Cookie trên thiết bị
if not st.session_state.logged_in and auth_cookie:
    all_data = load_all_data()
    if auth_cookie in all_data:
        st.session_state.logged_in = True
        st.session_state.username = auth_cookie

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
            remember_me = st.checkbox("Ghi nhớ đăng nhập trên thiết bị này", value=True)
            btn_login = st.form_submit_button("Đăng nhập")

            if btn_login:
                if user_input in all_data:
                    if all_data[user_input]["password"] == pass_input:
                        st.session_state.logged_in = True
                        st.session_state.username = user_input

                        # Nếu chọn Ghi nhớ -> Lưu cookie trong 30 ngày
                        if remember_me:
                            cookie_manager.set(
                                "user_auth", user_input, key="set_cookie", max_age=30 * 24 * 3600
                            )

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

    col_title, col_logout = st.columns([8, 2])
    with col_title:
        st.title(f"🎬 Quản Lý Thiết Bị & File - [{user}]")
    with col_logout:
        st.write("")
        if st.button("🚪 Đăng xuất"):
            # Xóa Cookie và Session khi bấm Đăng xuất
            cookie_manager.delete("user_auth", key="delete_cookie")
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
            st.info("Chưa có thiết bị nào trong hệ thống.")

        st.divider()

        # BỐ CỤC 3 CỘT: THÊM | CHỌN ĐỒ ĐI LÀM | GỘP SỬA & XÓA
        col_add, col_take, col_manage = st.columns(3)

        # 1. Thêm thiết bị mới
        with col_add:
            st.subheader("➕ Thêm thiết bị mới")
            with st.form("add_g_form"):
                g_name = st.text_input("Tên thiết bị")
                g_total = st.number_input(
                    "Tổng số lượng sở hữu", min_value=1, value=1, step=1
                )
                g_loc = st.text_input("Vị trí cất giữ / Ghi chú")
                btn_g_add = st.form_submit_button("Thêm mới")

                if btn_g_add and g_name:
                    gear_list.append({
                        "Tên thiết bị": g_name,
                        "Tổng số lượng": g_total,
                        "Đã mang đi": 0,
                        "Vị trí / Ghi chú": g_loc,
                    })
                    all_data[user]["gear"] = gear_list
                    save_all_data(all_data)
                    st.success(f"Đã thêm: {g_name}")
                    st.rerun()

        # 2. Chọn đồ đi làm (Cập nhật số lượng mang đi)
        with col_take:
            st.subheader("🚚 Chọn đồ đi làm")
            if gear_list:
                with st.form("take_g_form"):
                    selected_take = st.selectbox(
                        "Chọn thiết bị mang đi",
                        [item["Tên thiết bị"] for item in gear_list],
                    )
                    t_idx = next(
                        i
                        for i, item in enumerate(gear_list)
                        if item["Tên thiết bị"] == selected_take
                    )

                    max_qty = int(gear_list[t_idx]["Tổng số lượng"])
                    curr_taken = int(gear_list[t_idx]["Đã mang đi"])

                    if curr_taken > max_qty:
                        curr_taken = max_qty

                    new_taken = st.number_input(
                        f"Số lượng MANG ĐI (Bạn đang có: {max_qty})",
                        min_value=0,
                        value=curr_taken,
                        step=1,
                    )
                    btn_g_take = st.form_submit_button(
                        "Cập nhật trạng thái mang đi"
                    )

                    if btn_g_take:
                        if new_taken > max_qty:
                            st.error(f"❌ Lỗi: Bạn chỉ có tổng cộng {max_qty} cái, không thể mang đi {new_taken}!")
                        else:
                            gear_list[t_idx]["Đã mang đi"] = new_taken
                            all_data[user]["gear"] = gear_list
                            save_all_data(all_data)
                            st.success(f"Đã cập nhật cho {selected_take}!")
                            st.rerun()

        # 3. Gộp Sửa & Xóa thiết bị
        with col_manage:
            st.subheader("⚙️ Quản lý (Sửa / Xóa)")
            if gear_list:
                selected_m = st.selectbox(
                    "Chọn thiết bị muốn quản lý",
                    [item["Tên thiết bị"] for item in gear_list],
                    key="select_manage_gear",
                )
                m_idx = next(
                    i
                    for i, item in enumerate(gear_list)
                    if item["Tên thiết bị"] == selected_m
                )

                action = st.radio(
                    "Chọn thao tác:",
                    ["✏️ Chỉnh sửa thông tin", "🗑️ Xóa thiết bị"],
                    horizontal=True,
                )

                if action == "✏️ Chỉnh sửa thông tin":
                    with st.form("edit_g_form"):
                        e_name = st.text_input(
                            "Tên thiết bị",
                            value=gear_list[m_idx]["Tên thiết bị"],
                        )
                        e_total = st.number_input(
                            "Tổng số lượng sở hữu",
                            min_value=0,
                            value=int(gear_list[m_idx]["Tổng số lượng"]),
                            step=1,
                        )
                        e_taken = st.number_input(
                            "Số lượng đã mang đi",
                            min_value=0,
                            value=int(gear_list[m_idx]["Đã mang đi"]),
                            step=1,
                        )
                        e_loc = st.text_input(
                            "Vị trí / Ghi chú",
                            value=str(gear_list[m_idx]["Vị trí / Ghi chú"]),
                        )
                        btn_edit = st.form_submit_button("Lưu thay đổi")

                        if btn_edit:
                            if e_taken > e_total:
                                st.error("❌ Lỗi: Số lượng mang đi không được lớn hơn tổng số lượng!")
                            else:
                                gear_list[m_idx]["Tên thiết bị"] = e_name
                                gear_list[m_idx]["Tổng số lượng"] = e_total
                                gear_list[m_idx]["Đã mang đi"] = e_taken
                                gear_list[m_idx]["Vị trí / Ghi chú"] = e_loc
                                all_data[user]["gear"] = gear_list
                                save_all_data(all_data)
                                st.success("Đã cập nhật thông tin!")
                                st.rerun()

                elif action == "🗑️ Xóa thiết bị":
                    st.warning(f"Bạn có chắc muốn xóa '{selected_m}'?")
                    if st.button("❌ Xác nhận xóa vĩnh viễn", type="primary"):
                        user_data["gear"] = [
                            item
                            for item in gear_list
                            if item["Tên thiết bị"] != selected_m
                        ]
                        all_data[user] = user_data
                        save_all_data(all_data)
                        st.success(f"Đã xóa: {selected_m}")
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
        col_m_add, col_m_manage = st.columns(2)

        # Thêm file video
        with col_m_add:
            st.subheader("📝 Thêm file video mới")
            with st.form("add_m_form"):
                m_date = st.date_input("Ngày quay")
                m_proj = st.text_input("Tên dự án / Nội dung quay")
                m_store = st.text_input("Nơi lưu trữ (Ổ cứng, Cloud...)")
                m_type = st.selectbox(
                    "Định dạng", ["4K MP4", "1080p MP4", "RAW/LOG", "Khác"]
                )
                m_note = st.text_area("Ghi chú")
                btn_m_add = st.form_submit_button("Lưu thông tin File")

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

        # Gộp Sửa & Xóa File video
        with col_m_manage:
            st.subheader("⚙️ Quản lý File (Sửa / Xóa)")
            if media_list:
                selected_media = st.selectbox(
                    "Chọn dự án / file",
                    [item["Dự án / Tên Video"] for item in media_list],
                    key="select_manage_media",
                )
                media_idx = next(
                    i
                    for i, item in enumerate(media_list)
                    if item["Dự án / Tên Video"] == selected_media
                )

                m_action = st.radio(
                    "Chọn thao tác file:",
                    ["✏️ Chỉnh sửa thông tin", "🗑️ Xóa file"],
                    horizontal=True,
                    key="media_action_radio",
                )

                if m_action == "✏️ Chỉnh sửa thông tin":
                    with st.form("edit_m_form"):
                        e_m_proj = st.text_input(
                            "Tên dự án",
                            value=media_list[media_idx]["Dự án / Tên Video"],
                        )
                        e_m_store = st.text_input(
                            "Nơi lưu trữ",
                            value=str(media_list[media_idx]["Nơi lưu trữ"]),
                        )
                        e_m_type = st.text_input(
                            "Định dạng",
                            value=str(media_list[media_idx]["Định dạng"]),
                        )
                        e_m_note = st.text_area(
                            "Ghi chú",
                            value=str(media_list[media_idx]["Ghi chú"]),
                        )
                        btn_m_edit = st.form_submit_button("Lưu thay đổi")

                        if btn_m_edit:
                            media_list[media_idx]["Dự án / Tên Video"] = (
                                e_m_proj
                            )
                            media_list[media_idx]["Nơi lưu trữ"] = e_m_store
                            media_list[media_idx]["Định dạng"] = e_m_type
                            media_list[media_idx]["Ghi chú"] = e_m_note
                            all_data[user]["media"] = media_list
                            save_all_data(all_data)
                            st.success("Đã cập nhật file!")
                            st.rerun()

                elif m_action == "🗑️ Xóa file":
                    st.warning(f"Bạn có chắc muốn xóa dự án '{selected_media}'?")
                    if st.button(
                        "❌ Xác nhận xóa dự án này",
                        type="primary",
                        key="btn_del_media",
                    ):
                        user_data["media"] = [
                            item
                            for item in media_list
                            if item["Dự án / Tên Video"] != selected_media
                        ]
                        all_data[user] = user_data
                        save_all_data(all_data)
                        st.success(f"Đã xóa: {selected_media}")
                        st.rerun()

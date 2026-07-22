import extra_streamlit_components as stx
import pandas as pd
import streamlit as st
from supabase import create_client

# ------------------------------------------
# 1. CẤU HÌNH TRANG & KẾT NỐI SUPABASE
# ------------------------------------------
st.set_page_config(
    page_title="Hệ Thống Quản Lý Thiết Bị", page_icon="🎬", layout="wide"
)

# Lấy cấu hình kết nối từ Streamlit Secrets
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")


@st.cache_resource
def init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error(
            "⚠️ Chưa cấu hình Secrets (SUPABASE_URL và SUPABASE_KEY) trên"
            " Streamlit Cloud!"
        )
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = init_supabase()


# Khởi tạo Cookie Manager để lưu phiên đăng nhập
@st.cache_resource
def get_cookie_manager():
    return stx.CookieManager()


cookie_manager = get_cookie_manager()


# ------------------------------------------
# 2. CÁC HÀM XỬ LÝ DỮ LIỆU CƠ SỞ DỮ LIỆU
# ------------------------------------------
def load_user_data(username):
    """Tải thông tin của 1 user cụ thể từ Supabase"""
    try:
        res = (
            supabase.table("user_data")
            .select("*")
            .eq("username", username)
            .execute()
        )
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        st.error(f"Lỗi đọc dữ liệu từ Cloud: {e}")
        return None


def save_user_data(username, password, gear, media):
    """Thêm mới hoặc cập nhật dữ liệu user vào Supabase"""
    try:
        data = {
            "username": username,
            "password": password,
            "gear": gear,
            "media": media,
        }
        supabase.table("user_data").upsert(data).execute()
    except Exception as e:
        st.error(f"Lỗi lưu dữ liệu lên Cloud: {e}")


# ------------------------------------------
# 3. QUẢN LÝ PHIÊN ĐĂNG NHẬP (SESSION & COOKIE)
# ------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Kiểm tra cookie để tự động đăng nhập khi mở lại trang
auth_cookie = cookie_manager.get(cookie="user_auth")
if not st.session_state.logged_in and auth_cookie:
    user_info = load_user_data(auth_cookie)
    if user_info:
        st.session_state.logged_in = True
        st.session_state.username = auth_cookie

# ==========================================
# MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 Đăng Nhập Hệ Thống Quản Lý")
    tab_login, tab_register = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký tài khoản"])

    with tab_login:
        with st.form("login_form"):
            user_input = st.text_input("Tên đăng nhập").strip()
            pass_input = st.text_input("Mật khẩu", type="password").strip()
            remember_me = st.checkbox(
                "Ghi nhớ đăng nhập trên trình duyệt này", value=True
            )
            btn_login = st.form_submit_button("Đăng nhập")

            if btn_login:
                user_info = load_user_data(user_input)
                if user_info:
                    if user_info["password"] == pass_input:
                        st.session_state.logged_in = True
                        st.session_state.username = user_input

                        # Lưu cookie trong 30 ngày nếu chọn ghi nhớ
                        if remember_me:
                            cookie_manager.set(
                                "user_auth",
                                user_input,
                                key="set_cookie_login",
                                max_age=30 * 24 * 3600,
                            )

                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai mật khẩu!")
                else:
                    st.error("Tài khoản không tồn tại!")

    with tab_register:
        with st.form("register_form"):
            reg_user = st.text_input("Tạo tên đăng nhập mới").strip()
            reg_pass = st.text_input("Tạo mật khẩu", type="password").strip()
            btn_reg = st.form_submit_button("Tạo tài khoản")

            if btn_reg:
                if not reg_user or not reg_pass:
                    st.warning("Vui lòng điền đầy đủ thông tin!")
                else:
                    existing_user = load_user_data(reg_user)
                    if existing_user:
                        st.error("Tên đăng nhập này đã tồn tại!")
                    else:
                        save_user_data(reg_user, reg_pass, [], [])
                        st.success(
                            "Đăng ký thành công! Bạn có thể đăng nhập ngay."
                        )

# ==========================================
# MÀN HÌNH CHÍNH (SAU KHI ĐĂNG NHẬP)
# ==========================================
else:
    user = st.session_state.username
    user_info = load_user_data(user) or {
        "password": "",
        "gear": [],
        "media": [],
    }

    gear_list = user_info.get("gear", [])
    media_list = user_info.get("media", [])
    user_pass = user_info.get("password", "")

    col_title, col_logout = st.columns([8, 2])
    with col_title:
        st.title(f"🎬 Quản Lý Thiết Bị & File - [{user}]")
    with col_logout:
        st.write("")
        if st.button("🚪 Đăng xuất"):
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

        col_add, col_take, col_return, col_manage = st.columns(4)

        # 1. Thêm thiết bị mới
        with col_add:
            st.subheader("➕ Thêm mới")
            with st.form("add_g_form"):
                g_name = st.text_input("Tên thiết bị")
                g_total = st.number_input(
                    "Tổng số lượng", min_value=1, value=1, step=1
                )
                g_loc = st.text_input("Vị trí / Ghi chú")
                btn_g_add = st.form_submit_button("Thêm thiết bị")

                if btn_g_add and g_name:
                    gear_list.append({
                        "Tên thiết bị": g_name,
                        "Tổng số lượng": g_total,
                        "Đã mang đi": 0,
                        "Vị trí / Ghi chú": g_loc,
                    })
                    save_user_data(user, user_pass, gear_list, media_list)
                    st.success(f"Đã thêm: {g_name}")
                    st.rerun()

        # 2. Mang đồ đi làm
        with col_take:
            st.subheader("🚚 Mang đồ đi")
            if gear_list:
                with st.form("take_g_form"):
                    selected_take = st.selectbox(
                        "Chọn thiết bị đi làm",
                        [item["Tên thiết bị"] for item in gear_list],
                        key="sb_take_gear",
                    )
                    t_idx = next(
                        i
                        for i, item in enumerate(gear_list)
                        if item["Tên thiết bị"] == selected_take
                    )

                    max_qty = int(gear_list[t_idx]["Tổng số lượng"])
                    curr_taken = int(gear_list[t_idx]["Đã mang đi"])
                    available_qty = max_qty - curr_taken

                    st.caption(
                        f"Đang ở nhà: **{available_qty}** | Đã mang đi:"
                        f" **{curr_taken}**"
                    )

                    take_more = st.number_input(
                        "Số lượng mang đi thêm",
                        min_value=0,
                        max_value=max(0, available_qty),
                        value=0,
                        step=1,
                    )
                    btn_g_take = st.form_submit_button("Xác nhận mang đi")

                    if btn_g_take and take_more > 0:
                        gear_list[t_idx]["Đã mang đi"] = curr_taken + take_more
                        save_user_data(user, user_pass, gear_list, media_list)
                        st.success(
                            f"Đã mang đi thêm {take_more} {selected_take}!"
                        )
                        st.rerun()

        # 3. Trả đồ về kho (Chuyển về trạng thái sẵn sàng)
        with col_return:
            st.subheader("↩️ Trả đồ về kho")
            borrowed_gear = [
                item
                for item in gear_list
                if int(item.get("Đã mang đi", 0)) > 0
            ]

            if borrowed_gear:
                with st.form("return_g_form"):
                    selected_return = st.selectbox(
                        "Chọn thiết bị đã mang về",
                        [item["Tên thiết bị"] for item in borrowed_gear],
                        key="sb_return_gear",
                    )
                    r_idx = next(
                        i
                        for i, item in enumerate(gear_list)
                        if item["Tên thiết bị"] == selected_return
                    )

                    curr_taken = int(gear_list[r_idx]["Đã mang đi"])
                    st.caption(f"Đang mang đi ngoài đường: **{curr_taken}**")

                    return_qty = st.number_input(
                        "Số lượng trả về kho",
                        min_value=1,
                        max_value=curr_taken,
                        value=curr_taken,
                        step=1,
                    )
                    btn_g_return = st.form_submit_button("✅ Cất về kho")

                    if btn_g_return:
                        gear_list[r_idx]["Đã mang đi"] = (
                            curr_taken - return_qty
                        )
                        save_user_data(user, user_pass, gear_list, media_list)
                        st.success(
                            f"Đã cất {return_qty} {selected_return} về kho!"
                        )
                        st.rerun()
            else:
                st.info("Hiện không có thiết bị nào đang bị mang đi.")

        # 4. Quản lý (Sửa / Xóa)
        with col_manage:
            st.subheader("⚙️ Quản lý (Sửa/Xóa)")
            if gear_list:
                selected_m = st.selectbox(
                    "Chọn thiết bị",
                    [item["Tên thiết bị"] for item in gear_list],
                    key="select_manage_gear",
                )
                m_idx = next(
                    i
                    for i, item in enumerate(gear_list)
                    if item["Tên thiết bị"] == selected_m
                )

                action = st.radio(
                    "Thao tác:", ["✏️ Sửa", "🗑️ Xóa"], horizontal=True
                )

                if action == "✏️ Sửa":
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
                                st.error("❌ Số lượng mang đi vượt quá tổng số!")
                            else:
                                gear_list[m_idx]["Tên thiết bị"] = e_name
                                gear_list[m_idx]["Tổng số lượng"] = e_total
                                gear_list[m_idx]["Đã mang đi"] = e_taken
                                gear_list[m_idx]["Vị trí / Ghi chú"] = e_loc
                                save_user_data(
                                    user, user_pass, gear_list, media_list
                                )
                                st.success("Đã cập nhật!")
                                st.rerun()

                elif action == "🗑️ Xóa":
                    st.warning(f"Xóa '{selected_m}'?")
                    if st.button("❌ Xác nhận xóa", type="primary"):
                        gear_list = [
                            item
                            for item in gear_list
                            if item["Tên thiết bị"] != selected_m
                        ]
                        save_user_data(user, user_pass, gear_list, media_list)
                        st.success(f"Đã xóa: {selected_m}")
                        st.rerun()

    # ------------------------------------------
    # TAB 2: QUẢN LÝ FILE VIDEO
    # ------------------------------------------
    with tab2:
        st.header("Danh Sách File Video")
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

        # Thêm file video mới
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
                    save_user_data(user, user_pass, gear_list, media_list)
                    st.success("Đã lưu thành công!")
                    st.rerun()

        # Quản lý (Sửa/Xóa) file video
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
                    "Thao tác file:",
                    ["✏️ Chỉnh sửa", "🗑️ Xóa file"],
                    horizontal=True,
                    key="media_action_radio",
                )

                if m_action == "✏️ Chỉnh sửa":
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
                            save_user_data(
                                user, user_pass, gear_list, media_list
                            )
                            st.success("Đã cập nhật file!")
                            st.rerun()

                elif m_action == "🗑️ Xóa file":
                    st.warning(f"Xóa dự án '{selected_media}'?")
                    if st.button(
                        "❌ Xác nhận xóa", type="primary", key="btn_del_media"
                    ):
                        media_list = [
                            item
                            for item in media_list
                            if item["Dự án / Tên Video"] != selected_media
                        ]
                        save_user_data(user, user_pass, gear_list, media_list)
                        st.success(f"Đã xóa: {selected_media}")
                        st.rerun()

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

# Khởi tạo Cookie Manager
cookie_manager = stx.CookieManager()


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


def save_user_data(username, password, gear, media, payroll=None, members=None):
    """Thêm mới hoặc cập nhật dữ liệu user vào Supabase"""
    try:
        if payroll is None:
            payroll = []
        if members is None:
            members = []
        data = {
            "username": username,
            "password": password,
            "gear": gear,
            "media": media,
            "payroll": payroll,
            "members": members,
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

# Đọc cookie đăng nhập
auth_cookie = cookie_manager.get(cookie="user_auth")

if not st.session_state.logged_in and auth_cookie:
    user_info = load_user_data(auth_cookie)
    if user_info:
        st.session_state.logged_in = True
        st.session_state.username = auth_cookie

# ==========================================
# MÀN HÌNH ĐĂNG NHẬP / ĐĂNG KÝ / ĐỔI MẬT KHẨU NHANH
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 Hệ Thống Quản Lý - Xác Thực")
    tab_login, tab_register, tab_forgot = st.tabs([
        "🔑 Đăng nhập",
        "📝 Đăng ký tài khoản",
        "❓ Đổi / Khôi phục mật khẩu",
    ])

    # --- TAB ĐĂNG NHẬP ---
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

    # --- TAB ĐĂNG KÝ ---
    with tab_register:
        with st.form("register_form"):
            reg_user = st.text_input("Tạo tên đăng nhập mới").strip()
            reg_pass = st.text_input("Tạo mật khẩu", type="password").strip()
            btn_reg = st.form_submit_button("Tạo tài khoản")

            if btn_reg:
                if not reg_user or not reg_pass:
                    st.warning("Vui lòng điền đầy đủ tên đăng nhập và mật khẩu!")
                else:
                    existing_user = load_user_data(reg_user)
                    if existing_user:
                        st.error("Tên đăng nhập này đã tồn tại!")
                    else:
                        save_user_data(reg_user, reg_pass, [], [], [], [])
                        st.success("Đăng ký thành công! Hãy sang tab Đăng nhập.")

    # --- TAB ĐỔI / KHÔI PHỤC MẬT KHẨU ---
    with tab_forgot:
        st.markdown(
            "Vì web dùng nội bộ gia đình, bạn có thể nhập trực tiếp **Tên"
            " đăng nhập** và đặt **Mật khẩu mới** ngay lập tức."
        )
        with st.form("forgot_form"):
            f_user = st.text_input("Tên đăng nhập cần đổi mật khẩu").strip()
            f_new_pass = st.text_input(
                "Mật khẩu mới muốn đổi", type="password"
            ).strip()
            btn_reset = st.form_submit_button("Cập nhật mật khẩu mới")

            if btn_reset:
                if not f_user or not f_new_pass:
                    st.warning("Vui lòng điền đầy đủ thông tin!")
                else:
                    u_data = load_user_data(f_user)
                    if u_data:
                        save_user_data(
                            username=f_user,
                            password=f_new_pass,
                            gear=u_data.get("gear", []),
                            media=u_data.get("media", []),
                            payroll=u_data.get("payroll", []),
                            members=u_data.get("members", []),
                        )
                        st.success(
                            f"🎉 Đổi mật khẩu cho tài khoản '{f_user}' thành"
                            " công!"
                        )
                    else:
                        st.error("❌ Tên đăng nhập không tồn tại!")

# ==========================================
# MÀN HÌNH CHÍNH (SAU KHI ĐĂNG NHẬP)
# ==========================================
else:
    user = st.session_state.username
    user_info = load_user_data(user) or {
        "password": "",
        "gear": [],
        "media": [],
        "payroll": [],
        "members": [],
    }

    gear_list = user_info.get("gear", [])
    media_list = user_info.get("media", [])
    payroll_list = user_info.get("payroll", [])
    user_pass = user_info.get("password", "")
    members_list = user_info.get("members", [])

    # Tiêu đề và nút Thoát tài khoản
    col_title, col_logout = st.columns([7, 3])
    with col_title:
        st.title(f"🎬 Quản Lý Hệ Thống - [{user}]")
    with col_logout:
        st.write("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("⚙️ Cài đặt TK"):
                st.session_state.show_settings = (
                    not st.session_state.get("show_settings", False)
                )
        with col_btn2:
            if st.button("🚪 Thoát TK", type="primary"):
                cookie_manager.delete("user_auth")
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.show_settings = False
                st.rerun()

    # KHU VỰC CÀI ĐẶT TÀI KHOẢN
    if st.session_state.get("show_settings", False):
        with st.expander("🛠️ Cài đặt tài khoản & Đổi mật khẩu", expanded=True):
            with st.form("update_account_form"):
                st.write(f"Đang cấu hình cho tài khoản: **{user}**")
                up_pass = st.text_input(
                    "Nhập mật khẩu mới (để trống nếu giữ nguyên)",
                    type="password",
                )
                btn_save_acc = st.form_submit_button("Lưu thay đổi mật khẩu")

                if btn_save_acc:
                    final_pass = (
                        up_pass.strip() if up_pass.strip() else user_pass
                    )
                    save_user_data(
                        username=user,
                        password=final_pass,
                        gear=gear_list,
                        media=media_list,
                        payroll=payroll_list,
                        members=members_list,
                    )
                    st.success("✅ Cập nhật mật khẩu thành công!")
                    st.rerun()
        st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📦 1. Quản Lý Thiết Bị",
        "📁 2. Quản Lý File Video",
        "💰 3. Quản Lý Thành Viên & Tính Lương",
    ])

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
            df_gear["Số lần sử dụng"] = (
                pd.to_numeric(df_gear.get("Số lần sử dụng", 0), errors="coerce")
                .fillna(0)
                .astype(int)
            )
            df_gear["Còn dư ở nhà"] = (
                df_gear["Tổng số lượng"] - df_gear["Đã mang đi"]
            )
            df_gear["Trạng thái kho"] = df_gear["Còn dư ở nhà"].apply(
                lambda x: "🟢 Sẵn sàng"
                if x > 0
                else (
                    "🔴 Hết hàng / Đã mang đi" if x == 0 else "⚠️ Lỗi số lượng"
                )
            )
            if "Tình trạng máy" not in df_gear.columns:
                df_gear["Tình trạng máy"] = "✨ Tốt"

            # --- 1. KHUNG TÁCH RIÊNG: MÁY HỎNG / CẦN BẢO DƯỠNG ---
            df_issues = df_gear[
                df_gear["Tình trạng máy"].isin(
                    ["🛠️ Cần bảo dưỡng", "❌ Hỏng / Lỗi"]
                )
            ]
            if not df_issues.empty:
                st.error(
                    "⚠️ **CẢNH BÁO: CÓ THIẾT BỊ ĐANG GẶP VẤN ĐỀ / HỎNG HÓC!**"
                    " (Được tách riêng khỏi kho chính)"
                )
                st.dataframe(
                    df_issues[[
                        "Tên thiết bị",
                        "Tình trạng máy",
                        "Tổng số lượng",
                        "Đã mang đi",
                        "Số lần sử dụng",
                        "Vị trí / Ghi chú",
                    ]],
                    use_container_width=True,
                )
                st.markdown("---")

            # --- 2. BẢNG CHÍNH: TẤT CẢ HOẶC MÁY BÌNH THƯỜNG ---
            st.subheader("📋 Bảng Tổng Hợp Thiết Bị Kho")
            st.dataframe(
                df_gear[[
                    "Tên thiết bị",
                    "Tổng số lượng",
                    "Đã mang đi",
                    "Còn dư ở nhà",
                    "Trạng thái kho",
                    "Tình trạng máy",
                    "Số lần sử dụng",
                    "Vị trí / Ghi chú",
                ]],
                use_container_width=True,
            )
        else:
            st.info("Chưa có thiết bị nào trong hệ thống.")

        st.divider()

        col_add, col_take, col_return, col_manage = st.columns(4)

        with col_add:
            st.subheader("➕ Thêm mới")
            with st.form("add_g_form"):
                g_name = st.text_input("Tên thiết bị")
                g_total = st.number_input(
                    "Tổng số lượng", min_value=1, value=1, step=1
                )
                g_status = st.selectbox(
                    "Tình trạng máy",
                    ["✨ Tốt", "🛠️ Cần bảo dưỡng", "❌ Hỏng / Lỗi"],
                )
                g_loc = st.text_input("Vị trí / Ghi chú")
                btn_g_add = st.form_submit_button("Thêm thiết bị")

                if btn_g_add and g_name:
                    gear_list.append({
                        "Tên thiết bị": g_name,
                        "Tổng số lượng": g_total,
                        "Đã mang đi": 0,
                        "Số lần sử dụng": 0,
                        "Tình trạng máy": g_status,
                        "Vị trí / Ghi chú": g_loc,
                    })
                    save_user_data(
                        user,
                        user_pass,
                        gear_list,
                        media_list,
                        payroll_list,
                        members_list,
                    )
                    st.success(f"Đã thêm: {g_name}")
                    st.rerun()

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
                        current_uses = int(
                            gear_list[t_idx].get("Số lần sử dụng", 0)
                        )
                        gear_list[t_idx]["Số lần sử dụng"] = (
                            current_uses + take_more
                        )

                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            members_list,
                        )
                        st.success(
                            f"Đã mang đi thêm {take_more} {selected_take}!"
                        )
                        st.rerun()

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
                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            members_list,
                        )
                        st.success(
                            f"Đã cất {return_qty} {selected_return} về kho!"
                        )
                        st.rerun()
            else:
                st.info("Hiện không có thiết bị nào đang bị mang đi.")

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
                        e_uses = st.number_input(
                            "Số lần sử dụng",
                            min_value=0,
                            value=int(
                                gear_list[m_idx].get("Số lần sử dụng", 0)
                            ),
                            step=1,
                        )
                        current_status = gear_list[m_idx].get(
                            "Tình trạng máy", "✨ Tốt"
                        )
                        status_options = [
                            "✨ Tốt",
                            "🛠️ Cần bảo dưỡng",
                            "❌ Hỏng / Lỗi",
                        ]
                        status_idx = (
                            status_options.index(current_status)
                            if current_status in status_options
                            else 0
                        )
                        e_status = st.selectbox(
                            "Tình trạng máy",
                            status_options,
                            index=status_idx,
                        )
                        e_loc = st.text_input(
                            "Vị trí / Ghi chú",
                            value=str(gear_list[m_idx]["Vị trí / Ghi chú"]),
                        )
                        btn_edit = st.form_submit_button("Lưu thay đổi")

                        if btn_edit:
                            if e_taken > e_total:
                                st.error(
                                    "❌ Số lượng mang đi vượt quá tổng số!"
                                )
                            else:
                                gear_list[m_idx]["Tên thiết bị"] = e_name
                                gear_list[m_idx]["Tổng số lượng"] = e_total
                                gear_list[m_idx]["Đã mang đi"] = e_taken
                                gear_list[m_idx]["Số lần sử dụng"] = e_uses
                                gear_list[m_idx]["Tình trạng máy"] = e_status
                                gear_list[m_idx]["Vị trí / Ghi chú"] = e_loc
                                save_user_data(
                                    user,
                                    user_pass,
                                    gear_list,
                                    media_list,
                                    payroll_list,
                                    members_list,
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
                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            members_list,
                        )
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
                    save_user_data(
                        user,
                        user_pass,
                        gear_list,
                        media_list,
                        payroll_list,
                        members_list,
                    )
                    st.success("Đã lưu thành công!")
                    st.rerun()

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
                                user,
                                user_pass,
                                gear_list,
                                media_list,
                                payroll_list,
                                members_list,
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
                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            members_list,
                        )
                        st.success(f"Đã xóa: {selected_media}")
                        st.rerun()

    # ------------------------------------------
    # TAB 3: QUẢN LÝ THÀNH VIÊN & TIỀN LƯƠNG
    # ------------------------------------------
    with tab3:
        st.header("👥 Quản Lý Thành Viên & Tính Lương")

        with st.expander("⚙️ Cài đặt danh sách Thành viên", expanded=True):
            col_m_view, col_m_add_box = st.columns(2)

            with col_m_view:
                st.write("**Xóa thành viên khỏi danh sách:**")
                if members_list:
                    with st.form("delete_member_form"):
                        member_to_delete = st.selectbox(
                            "Chọn thành viên cần xóa", members_list
                        )
                        btn_del_member = st.form_submit_button(
                            "🗑️ Xóa thành viên này"
                        )

                        if btn_del_member and member_to_delete:
                            members_list.remove(member_to_delete)
                            save_user_data(
                                user,
                                user_pass,
                                gear_list,
                                media_list,
                                payroll_list,
                                members_list,
                            )
                            st.success(
                                f"Đã xóa thành viên: {member_to_delete}"
                            )
                            st.rerun()
                else:
                    st.info("Chưa có thành viên nào.")

            with col_m_add_box:
                st.write("**Thêm thành viên mới:**")
                with st.form("add_member_form"):
                    new_member_name = st.text_input(
                        "Tên thành viên mới", placeholder="Nhập tên..."
                    ).strip()
                    btn_add_member = st.form_submit_button(
                        "➕ Thêm thành viên"
                    )

                    if btn_add_member:
                        if new_member_name:
                            if new_member_name not in members_list:
                                members_list.append(new_member_name)
                                save_user_data(
                                    user,
                                    user_pass,
                                    gear_list,
                                    media_list,
                                    payroll_list,
                                    members_list,
                                )
                                st.success(
                                    f"Đã thêm thành viên: {new_member_name}"
                                )
                                st.rerun()
                            else:
                                st.warning("Thành viên này đã tồn tại!")
                        else:
                            st.warning("Vui lòng nhập tên thành viên!")

        st.divider()

        df_payroll = pd.DataFrame(payroll_list)

        if not df_payroll.empty:
            df_payroll["Số tiền (VNĐ)"] = (
                pd.to_numeric(df_payroll["Số tiền (VNĐ)"], errors="coerce")
                .fillna(0)
                .astype(int)
            )

            st.subheader("📋 Bảng Lịch Sử Yêu Cầu & Chi Phí Phát Sinh")
            st.dataframe(df_payroll, use_container_width=True)

            st.subheader("📊 Tổng Kết Tiền Lương Cần Trả Cuối Tháng")
            summary_df = (
                df_payroll.groupby("Tên nhân viên")["Số tiền (VNĐ)"]
                .sum()
                .reset_index()
            )
            summary_df.columns = ["Thành viên", "Tổng lương tích lũy"]

            summary_df["Tổng lương tích lũy (VNĐ)"] = summary_df[
                "Tổng lương tích lũy"
            ].apply(lambda x: f"{x:,.0f} đ")
            st.table(summary_df[["Thành viên", "Tổng lương tích lũy (VNĐ)"]])
        else:
            st.info("Chưa có phát sinh công việc hoặc tiền lương nào.")

        st.divider()
        col_p_add, col_p_manage = st.columns(2)

        with col_p_add:
            st.subheader("➕ Thêm Tiền Lương / Khoản Phát Sinh")
            with st.form("add_payroll_form"):
                p_date = st.date_input("Ngày thực hiện / yêu cầu")

                if members_list:
                    p_name = st.selectbox(
                        "Chọn thành viên", members_list
                    ).strip()
                else:
                    p_name = st.text_input(
                        "Tên thành viên (Chưa có danh sách, hãy nhập tên)"
                    ).strip()

                p_task = st.text_input("Nội dung công việc / Khoản phát sinh")
                p_salary = st.number_input(
                    "Số tiền (VNĐ)", min_value=0, value=200000, step=50000
                )
                btn_p_submit = st.form_submit_button(
                    "➕ Thêm khoản tiền lương này"
                )

                if btn_p_submit:
                    if p_name and p_task:
                        payroll_list.append({
                            "Ngày": str(p_date),
                            "Tên nhân viên": p_name,
                            "Nội dung công việc": p_task,
                            "Số tiền (VNĐ)": p_salary,
                        })
                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            members_list,
                        )
                        st.success(
                            f"Đã thêm khoản chi {p_salary:,.0f} đ cho {p_name}!"
                        )
                        st.rerun()
                    else:
                        st.warning(
                            "Vui lòng điền đầy đủ tên thành viên và nội dung!"
                        )

        with col_p_manage:
            st.subheader("⚙️ Quản Lý / Xóa Khoản Chi")
            if payroll_list:
                with st.form("delete_payroll_form"):
                    payroll_options = [
                        f"{i}: [{item.get('Ngày', '')}] - {item.get('Tên nhân viên', '')} - {item.get('Nội dung công việc', '')} ({item.get('Số tiền (VNĐ)', 0):,.0f}đ)"
                        for i, item in enumerate(payroll_list)
                    ]
                    selected_payroll_to_del = st.selectbox(
                        "Chọn mục cần xóa", payroll_options
                    )
                    btn_del_payroll = st.form_submit_button(
                        "🗑️ Xóa khoản chi này"
                    )

                    if btn_del_payroll:
                        idx_to_del = int(
                            selected_payroll_to_del.split(":")[0]
                        )
                        payroll_list.pop(idx_to_del)
                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            members_list,
                        )
                        st.success("Đã xóa khoản chi thành công!")
                        st.rerun()
            else:
                st.info("Không có khoản chi nào để quản lý.")

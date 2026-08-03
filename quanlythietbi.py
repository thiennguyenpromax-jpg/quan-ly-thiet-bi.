if btn_p_submit and p_name and p_task:
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
                        current_gmail,
                        members_list,
                    )
                    st.success(f"Đã thêm khoản chi cho {p_name} thành công!")
                    st.rerun()
                elif btn_p_submit:
                    st.warning("Vui lòng điền đầy đủ tên thành viên và nội dung công việc!")

        # 2. Quản lý (Xóa/Chỉnh sửa) các khoản lương/phát sinh
        with col_p_manage:
            st.subheader("⚙️ Quản lý Khoản Lương / Chi Phí")
            if payroll_list:
                with st.form("manage_payroll_form"):
                    # Tạo nhãn định danh cho từng dòng lịch sử lương để chọn dễ hơn
                    payroll_options = [
                        f"{i}: [{item.get('Ngày')}] - {item.get('Tên nhân viên')} - {item.get('Nội dung công việc')} ({item.get('Số tiền (VNĐ)'):,.0f}đ)"
                        for i, item in enumerate(payroll_list)
                    ]
                    selected_payroll_str = st.selectbox("Chọn mục cần xóa", payroll_options)
                    btn_del_payroll = st.form_submit_button("🗑️ Xóa khoản này", type="primary")

                    if btn_del_payroll:
                        idx_to_delete = int(selected_payroll_str.split(":")[0])
                        removed_item = payroll_list.pop(idx_to_delete)
                        save_user_data(
                            user,
                            user_pass,
                            gear_list,
                            media_list,
                            payroll_list,
                            current_gmail,
                            members_list,
                        )
                        st.success(f"Đã xóa khoản chi của: {removed_item.get('Tên nhân viên')}")
                        st.rerun()
            else:
                st.info("Không có khoản lương hay chi phí nào để quản lý.")

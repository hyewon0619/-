package com.example.mentos.Login;

import android.os.Bundle;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import android.os.Handler;
import android.text.Editable;
import android.text.InputType;
import android.text.TextWatcher;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioGroup;
import android.widget.TextView;

import com.android.volley.RequestQueue;
import com.android.volley.Response;
import com.android.volley.toolbox.Volley;
import com.example.mentos.R;

import org.json.JSONException;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;

public class SigninActivity extends AppCompatActivity {

    private static String IP_ADDRESS = "http://52.79.234.36:5001/signup";
    private static String TAG = "phpsignup";

    private EditText emailID;
    private EditText pwd;
    private EditText pwdCheck;
    private EditText birth;
    private TextView pwdCheckWarning;

    Button submit;
    RadioGroup radioGroup;
    String gender = "";

    private AlertDialog dialog;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.signin);

        emailID = findViewById(R.id.sign_email);
        pwd = findViewById(R.id.sign_pwd);
        pwd.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        pwdCheck = findViewById(R.id.sign_pwd_check);
        pwdCheck.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        pwdCheckWarning = findViewById(R.id.pwd_check_warning);
        birth = findViewById(R.id.sign_birth);
        radioGroup = findViewById(R.id.genderGroup);

        // 비밀번호 확인 필드에 TextWatcher 추가
        pwdCheck.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                validatePassword();
            }

            @Override
            public void afterTextChanged(Editable s) {}
        });


        // 성별 기입
        radioGroup.setOnCheckedChangeListener(new RadioGroup.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(RadioGroup group, int checkedId) {
                if (checkedId == R.id.maleButton) {
                    gender = "male";
                } else if (checkedId == R.id.femaleButton) {
                    gender = "female";
                }
            }
        });


        // 생년월일 입력 시 자동으로 "-" 추가
        birth.addTextChangedListener(new TextWatcher() {
            private String current = "";
            private String ddmmyyyy = "YYYYMMDD";
            private SimpleDateFormat dateFormat = new SimpleDateFormat("YYYYMMDD", Locale.KOREA);

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                if (!s.toString().equals(current)) {
                    String clean = s.toString().replaceAll("[^\\d]", "");
                    String cleanC = current.replaceAll("[^\\d]", "");

                    int cl = clean.length();
                    int sel = cl;
                    for (int i = 2; i <= cl && i < 6; i += 2) {
                        sel++;
                    }
                    //Fix for pressing delete next to a forward slash
                    if (clean.equals(cleanC)) sel--;

                    if (clean.length() < 8) {
                        clean = clean + ddmmyyyy.substring(clean.length());
                    } else {
                        //This part makes sure that when we finish entering numbers
                        //the date is correct, fixing it otherwise
                        int year  = Integer.parseInt(clean.substring(0,4));
                        int mon  = Integer.parseInt(clean.substring(4,6));
                        int day = Integer.parseInt(clean.substring(6,8));

                        mon = mon < 1 ? 1 : mon > 12 ? 12 : mon;
                        Calendar cal = Calendar.getInstance();
                        cal.set(Calendar.MONTH, mon-1);
                        year = (year<1900)?1900:(year>2100)?2100:year;
                        cal.set(Calendar.YEAR, year);
                        // ^ first set year for the line below to work correctly
                        day = (day > cal.getActualMaximum(Calendar.DATE))? cal.getActualMaximum(Calendar.DATE):day;
                        clean = String.format("%02d%02d%02d",year, mon, day);
                    }

                    clean = String.format("%s-%s-%s", clean.substring(0, 4),
                            clean.substring(4, 6),
                            clean.substring(6, 8));

                    sel = sel < 0 ? 0 : sel;
                    current = clean;
                    birth.setText(current);
                    birth.setSelection(sel < current.length() ? sel : current.length());
                }
            }

            @Override
            public void afterTextChanged(Editable s) {}

            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
        });


        Button signinButton = findViewById(R.id.signin_button);
        signinButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String email = emailID.getText().toString();
                String password = pwd.getText().toString();
                String confirmPassword = pwdCheck.getText().toString();
                String birthdate = birth.getText().toString();

                if(email.equals("") || password.equals("") || birth.equals("") || gender.equals(""))
                {
                    AlertDialog.Builder builder = new AlertDialog.Builder(SigninActivity.this);
                    dialog = builder.setMessage("빈 칸 없이 입력해주세요.")
                            .setNegativeButton("확인", null)
                            .create();
                    dialog.show();
                    return;
                }

                if (!password.equals(confirmPassword)) {
                    pwdCheckWarning.setVisibility(View.VISIBLE);
                    pwdCheckWarning.setText("비밀번호가 일치하지 않습니다.");
                    pwdCheckWarning.setTextColor(getResources().getColor(android.R.color.holo_red_dark));
                    return;
                } else {
                    pwdCheckWarning.setVisibility(View.GONE);
                }

                Log.d("Register", "Register request started");


                Response.Listener<JSONObject> responseListener = new Response.Listener<JSONObject>() {
                    @Override
                    public void onResponse(JSONObject response) {
                        // 서버 응답 로그
                        Log.d("Register", "Response: " + response.toString());

                        try {
                            String message = response.getString("message");
                            if ("User created successfully!".equals(message)) {
                                runOnUiThread(new Runnable() {
                                    @Override
                                    public void run() {
                                        AlertDialog.Builder builder = new AlertDialog.Builder(SigninActivity.this);
                                        builder.setMessage("회원 등록에 성공했습니다.");
//                                                .setNegativeButton("확인", null);

                                        final AlertDialog alertDialog = builder.create();
                                        alertDialog.show();

                                        // 1초 후에 AlertDialog를 닫는 Handler 추가
                                        new Handler().postDelayed(new Runnable() {
                                            @Override
                                            public void run() {
                                                if (alertDialog.isShowing()) {
                                                    alertDialog.dismiss();
                                                    finish(); // 화면을 종료하고 싶다면 finish() 호출
                                                }
                                            }
                                        }, 600); // 1초(1000ms) 지연
                                    }
                                });
                            } else {
                                runOnUiThread(new Runnable() {
                                    @Override
                                    public void run() {
                                        AlertDialog.Builder builder = new AlertDialog.Builder(SigninActivity.this);
                                        builder.setMessage("회원 등록에 실패했습니다.")
                                                .setNegativeButton("확인", null)
                                                .show();
                                    }
                                });
                            }

                        }
                        catch (JSONException e)
                        {
                            e.printStackTrace();
                            // JSON 파싱 에러 로그
                            Log.e("Register", "JSON parsing error: " + e.getMessage());
                        }
                    }
                };

                try {
                    RegisterRequest registerRequest = new RegisterRequest(email, password, gender, birthdate, responseListener);
                    RequestQueue queue = Volley.newRequestQueue(SigninActivity.this);
                    queue.add(registerRequest);
                } catch (JSONException e) {
                    e.printStackTrace();
                }


//                if (validatePassword()) {
//                    String email = emailID.getText().toString();
//                    String password = pwd.getText().toString();
//                    String Birth = birth.getText().toString();
//
//                    InsertData task = new InsertData();
//                    task.execute("http://" + IP_ADDRESS + "/insert.php", email, password, gender, Birth);
//
//                    emailID.setText("");
//                    pwd.setText("");
//                    pwdCheck.setText("");
//                    birth.setText("");
//                }
            }
        });


    }

    private boolean validatePassword() {
        String password = pwd.getText().toString();
        String confirmPassword = pwdCheck.getText().toString();

        if (!password.equals(confirmPassword)) {
            pwdCheckWarning.setVisibility(View.VISIBLE);
            pwdCheckWarning.setText("비밀번호가 일치하지 않습니다.");
            pwdCheckWarning.setTextColor(getResources().getColor(android.R.color.holo_red_dark));
            return false;
        } else {
            pwdCheckWarning.setVisibility(View.GONE);
            return true;
        }
    }








//    class InsertData extends AsyncTask<String, Void, String> {
//        ProgressDialog progressDialog;
//
//        @Override
//        protected void onPreExecute() {
//            super.onPreExecute();
//
//            progressDialog = ProgressDialog.show(signin.this,
//                    "Please Wait", null, true, true);
//        }
//
//        @Override
//        protected void onPostExecute(String result) {
//            super.onPostExecute(result);
//
//            progressDialog.dismiss();
//            Log.d(TAG, "POST response  - " + result);
//
//            showResult(result); // Call the new showResult method
//        }
//
//        @Override
//        protected String doInBackground(String... params) {
//            String email = params[1];
//            String password = params[2];
//            String gender = params[3];
//            String birthdate = params[4];
//
//            String serverURL = params[0];
//            String postParameters = "email=" + email + "&password=" + password + "&gender=" + gender + "&birthdate=" + birthdate;
//
//            try {
//                URL url = new URL(serverURL);
//                HttpURLConnection httpURLConnection = (HttpURLConnection) url.openConnection();
//
//                httpURLConnection.setReadTimeout(5000);
//                httpURLConnection.setConnectTimeout(5000);
//                httpURLConnection.setRequestMethod("POST");
//                httpURLConnection.connect();
//
//                OutputStream outputStream = httpURLConnection.getOutputStream();
//                outputStream.write(postParameters.getBytes("UTF-8"));
//                outputStream.flush();
//                outputStream.close();
//
//                int responseStatusCode = httpURLConnection.getResponseCode();
//                Log.d(TAG, "POST response code - " + responseStatusCode);
//
//                InputStream inputStream;
//                if (responseStatusCode == HttpURLConnection.HTTP_OK) {
//                    inputStream = httpURLConnection.getInputStream();
//                } else {
//                    inputStream = httpURLConnection.getErrorStream();
//                }
//
//                InputStreamReader inputStreamReader = new InputStreamReader(inputStream, "UTF-8");
//                BufferedReader bufferedReader = new BufferedReader(inputStreamReader);
//
//                StringBuilder sb = new StringBuilder();
//                String line;
//
//                while ((line = bufferedReader.readLine()) != null) {
//                    sb.append(line);
//                }
//
//                bufferedReader.close();
//
//                return sb.toString();
//
//            } catch (Exception e) {
//                Log.d(TAG, "InsertData: Error ", e);
//                return new String("Error: " + e.getMessage());
//            }
//        }
//
//        private void showResult(String jsonString) {
//            String TAG_JSON = "webnautes";
//            String TAG_EMAIL = "email";
//            String TAG_PASSWORD = "password";
//            String TAG_GENDER = "gender";
//            String TAG_BIRTHDATE = "birthdate";
//
//            try {
//                // 서버 응답을 로그로 출력하여 확인
//                Log.d("ServerResponse", jsonString);
//
//                // 서버 응답이 빈 문자열인지 확인
//                if (jsonString == null || jsonString.isEmpty()) {
//                    Log.e("JSONError", "Response is empty or null");
//                    return;
//                }
//                // JSON 객체로 변환 시도
//                JSONObject jsonObject = new JSONObject(jsonString);
//
//                // 예상되는 JSON 배열을 추출
//                JSONArray jsonArray = jsonObject.getJSONArray(TAG_JSON);
//
//                for (int i = 0; i < jsonArray.length(); i++) {
//                    JSONObject item = jsonArray.getJSONObject(i);
//
//                    String email = item.getString(TAG_EMAIL);
//                    String password = item.getString(TAG_PASSWORD);
//                    String gender = item.getString(TAG_GENDER);
//                    String birthdate = item.getString(TAG_BIRTHDATE);
//
//                    UserData userData = new UserData(email, password, gender, birthdate);
//                    // Add the userData object to your data list or update the UI accordingly
//
//                    // Example: Assuming you have a list and adapter
//                    // mArrayList.add(userData);
//                    // mAdapter.notifyDataSetChanged();
//                }
//
//                Toast.makeText(signin.this, "Data parsed successfully", Toast.LENGTH_LONG).show();
//
//            } catch (JSONException e) {
//                Log.d(TAG, "showResult : ", e);
//                Toast.makeText(signin.this, "Error parsing data", Toast.LENGTH_LONG).show();
//            } catch (Exception e) {
//                // 기타 예외 처리
//                Log.e("Error", "Unexpected error: " + e.getMessage());
//                e.printStackTrace();
//            }
//        }
//    }
//
//    class UserData {
//        private String email;
//        private String password;
//        private String gender;
//        private String birthdate;
//
//        public UserData(String email, String password, String gender, String birthdate) {
//            this.email = email;
//            this.password = password;
//            this.gender = gender;
//            this.birthdate= birthdate;
//        }
//
//        // Getters and setters
//        public String getEmail() { return email; }
//        public void setEmail(String email) { this.email = email; }
//        public String getPassword() { return password; }
//        public void setPassword(String password) { this.password = password; }
//        public String getGender() { return gender; }
//        public void setGender(String gender) { this.gender = gender; }
//        public String getBirthdate() { return birthdate; }
//        public void setBirthdate(String birthdate) { this.birthdate = birthdate; }
//    }

    @Override
    protected void onStop() {
        super.onStop();
        if(dialog != null)
        {
            dialog.dismiss();
            dialog = null;
        }
    }

}
